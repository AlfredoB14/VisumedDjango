import requests
from collections import Counter
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_GET

# Configuracion de Orthanc
ORTHANC_URL = settings.ORTHANC_URL


def _orthanc_timeout_seconds():
    try:
        return max(5, int(getattr(settings, 'ORTHANC_HTTP_TIMEOUT', 20)))
    except (TypeError, ValueError):
        return 20


def _orthanc_auth():
    user = getattr(settings, 'ORTHANC_USER', None)
    password = getattr(settings, 'ORTHANC_PASS', None)
    if user and password:
        return (user, password)
    return None


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return default


def _parse_pixel_spacing(value):
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split('\\')
    elif isinstance(value, list):
        parts = value
    else:
        return None

    if len(parts) != 2:
        return None

    try:
        return [float(parts[0]), float(parts[1])]
    except (TypeError, ValueError):
        return None


def _extract_pixel_spacing_from_tags(tags):
    if not isinstance(tags, dict):
        return None
    return (
        _parse_pixel_spacing(tags.get('PixelSpacing'))
        or _parse_pixel_spacing(tags.get('ImagerPixelSpacing'))
    )


def _get_instance_pixel_spacing(instance_id):
    response = orthanc_request(f"/instances/{instance_id}/simplified-tags")
    if not response:
        return None
    try:
        tags = response.json()
    except ValueError:
        return None
    return _extract_pixel_spacing_from_tags(tags)


def _get_series_pixel_spacing(series_id):
    response = orthanc_request(f"/series/{series_id}/shared-tags")
    if not response:
        return None
    try:
        tags = response.json()
    except ValueError:
        return None
    return _extract_pixel_spacing_from_tags(tags)


def _get_series_number(series_id):
    response = orthanc_request(f"/series/{series_id}")
    if not response:
        return 0
    try:
        series_data = response.json()
    except ValueError:
        return 0

    tags = series_data.get('MainDicomTags', {})
    if not isinstance(tags, dict):
        tags = {}
    return _safe_int(tags.get('SeriesNumber'), 0)


def _normalize_pixel_spacing(spacing, decimals=6):
    if not spacing or len(spacing) != 2:
        return None
    return (round(float(spacing[0]), decimals), round(float(spacing[1]), decimals))


def _compute_general_pixel_spacing(instances):
    normalized_values = []
    for item in instances:
        normalized = _normalize_pixel_spacing(item.get('pixel_spacing'))
        if normalized is not None:
            normalized_values.append(normalized)

    if not normalized_values:
        return None

    most_common_spacing, _ = Counter(normalized_values).most_common(1)[0]
    return [most_common_spacing[0], most_common_spacing[1]]


def _resolve_general_pixel_spacing(sorted_instances, series_pixel_spacing_cache):
    # 1) Reusa cualquier spacing ya encontrado en MainDicomTags.
    if series_pixel_spacing_cache:
        first_series_id = next(iter(series_pixel_spacing_cache))
        spacing = series_pixel_spacing_cache.get(first_series_id)
        if spacing is not None:
            return _normalize_pixel_spacing(spacing)

    # 2) Intenta una sola vez por serie con shared-tags.
    for item in sorted_instances:
        series_id = item.get('series_id')
        if not series_id:
            continue

        if series_id not in series_pixel_spacing_cache:
            series_pixel_spacing_cache[series_id] = _get_series_pixel_spacing(series_id)

        spacing = series_pixel_spacing_cache.get(series_id)
        if spacing is not None:
            return _normalize_pixel_spacing(spacing)

    # 3) Fallback final: una sola instancia.
    for item in sorted_instances:
        instance_id = item.get('id')
        if not instance_id:
            continue
        spacing = _get_instance_pixel_spacing(instance_id)
        if spacing is not None:
            return _normalize_pixel_spacing(spacing)

    return None


def _stream_content(response, chunk_size=65536):
    try:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
    finally:
        response.close()


def orthanc_request(path, method="GET", data=None, params=None, stream=False):
    """Realiza solicitudes al servidor Orthanc."""
    url = f"{ORTHANC_URL}{path}"
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            auth=_orthanc_auth(),
            timeout=_orthanc_timeout_seconds(),
            stream=stream,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a Orthanc: {e}")
        return None


@require_GET
def get_study_images(request, study_id):
    """Devuelve todas las imagenes de un estudio ordenadas por serie e instancia."""
    try:
        quality = request.GET.get('quality', 25)
        try:
            quality = int(quality)
        except (ValueError, TypeError):
            quality = 25

        response = orthanc_request(f"/studies/{study_id}/instances")
        if not response:
            return JsonResponse({"error": "No se pudo obtener las instancias del estudio"}, status=500)

        instances = response.json()
        if not isinstance(instances, list):
            return JsonResponse({"error": "Orthanc devolvio un formato inesperado"}, status=502)

        series_numbers = {}
        series_pixel_spacing_cache = {}

        instances_with_numbers = []
        for instance in instances:
            if not isinstance(instance, dict):
                continue

            instance_id = instance.get("ID")
            series_id = instance.get("ParentSeries")
            tags = instance.get('MainDicomTags', {})
            if not isinstance(tags, dict):
                tags = {}

            if not instance_id or not series_id:
                continue

            if series_id not in series_numbers:
                # Prioriza el valor de serie en /series/{id}, que es mas confiable
                # que MainDicomTags a nivel instancia para ordenamiento global.
                series_numbers[series_id] = _get_series_number(series_id)

            pixel_spacing = _extract_pixel_spacing_from_tags(tags)
            if pixel_spacing is not None and series_id not in series_pixel_spacing_cache:
                series_pixel_spacing_cache[series_id] = pixel_spacing

            instance_info = {
                "id": instance_id,
                "series_id": series_id,
                "series_number": series_numbers.get(series_id, 0),
                "instance_number": _safe_int(tags.get('InstanceNumber'), 0),
            }
            instances_with_numbers.append(instance_info)

        sorted_instances = sorted(
            instances_with_numbers,
            key=lambda x: (
                x["series_number"],
                x["series_id"],
                x["instance_number"],
                x["id"],
            ),
        )

        general_pixel_spacing = _resolve_general_pixel_spacing(
            sorted_instances,
            series_pixel_spacing_cache,
        )

        image_urls = []
        for instance in sorted_instances:
            image_url = f"{ORTHANC_URL}/instances/{instance['id']}/frames/0/rendered?quality={quality}"
            image_info = {
                "instanceId": instance['id'],
                "imageUrl": image_url,
                "seriesNumber": instance["series_number"],
                "instanceNumber": instance["instance_number"],
            }

            image_urls.append(image_info)

        return JsonResponse(
            {
                "studyId": study_id,
                "imageCount": len(image_urls),
                "pixelSpacing": list(general_pixel_spacing) if general_pixel_spacing else None,
                "images": image_urls,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_rendered_instance(request, instance_id):
    """Devuelve una imagen renderizada de una instancia DICOM especifica."""
    try:
        quality = request.GET.get('quality', 90)
        try:
            quality = int(quality)
        except (ValueError, TypeError):
            quality = 90

        response = orthanc_request(
            f"/instances/{instance_id}/rendered",
            params={"quality": quality},
            stream=True,
        )
        if not response:
            return JsonResponse({"error": "No se pudo obtener la imagen"}, status=500)

        return StreamingHttpResponse(
            _stream_content(response),
            content_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=instance-{instance_id}.jpg",
                "Cache-Control": "public, max-age=86400, stale-while-revalidate=60",
            },
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_study_metadata(request, study_id):
    """Devuelve los metadatos de un estudio DICOM."""
    try:
        response = orthanc_request(f"/studies/{study_id}")
        if not response:
            return JsonResponse({"error": "No se pudo obtener los metadatos del estudio"}, status=500)

        shared_tags_response = orthanc_request(f"/studies/{study_id}/shared-tags")
        shared_tags = shared_tags_response.json() if shared_tags_response else {}

        metadata = response.json()
        metadata["SharedTags"] = shared_tags

        return JsonResponse(metadata)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_all_studies(request):
    """Devuelve la lista de todos los estudios disponibles en Orthanc."""
    try:
        response = orthanc_request("/studies")
        if not response:
            return JsonResponse({"error": "No se pudo obtener la lista de estudios"}, status=500)

        studies = response.json()

        if request.GET.get('expand', 'false').lower() == 'true':
            detailed_studies = []
            for study_id in studies:
                study_info_response = orthanc_request(f"/studies/{study_id}")
                if study_info_response:
                    detailed_studies.append(study_info_response.json())
            return JsonResponse(detailed_studies, safe=False)

        return JsonResponse(studies, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
