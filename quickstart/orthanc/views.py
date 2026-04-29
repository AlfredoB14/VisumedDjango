from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

import numpy as np
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .integration.views import (
    get_all_studies,
    get_rendered_instance,
    get_study_images,
    get_study_metadata,
    orthanc_request,
)
from .clinical.views import (
    doctor_detail,
    doctors_collection,
    patient_detail,
    patients_collection,
    report_detail,
    reports_collection,
    studies_collection,
    study_detail,
)

__all__ = [
    'orthanc_request',
    'get_all_studies',
    'get_study_images',
    'get_study_metadata',
    'get_rendered_instance',
    'doctors_collection',
    'doctor_detail',
    'patients_collection',
    'patient_detail',
    'studies_collection',
    'study_detail',
    'reports_collection',
    'report_detail',
    'classify_plane',
    'parse_orientation',
    'parse_position',
    'parse_instance_number',
    'compute_slice_position',
    'fetch_series_tags',
    'StudyImagesIndexView',
    'BaseStudyPlaneView',
    'StudyAxialView',
    'StudySagittalView',
    'StudyCoronalView',
    'StudyDebugView',
]


PLANES = ('axial', 'sagittal', 'coronal')


def _is_truthy(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _cache_ttl_seconds():
    try:
        return max(30, int(getattr(settings, 'ORTHANC_STUDY_INDEX_CACHE_TTL', 300)))
    except (TypeError, ValueError):
        return 300


def _max_workers():
    try:
        value = int(getattr(settings, 'ORTHANC_STUDY_INDEX_MAX_WORKERS', 3))
    except (TypeError, ValueError):
        value = 3
    return min(8, max(1, value))


def _study_cache_key(orthanc_study_id):
    return f"orthanc:study-image-index:v4:{orthanc_study_id}"


def classify_plane(orientation):
    """
    Classify the plane based on ImageOrientationPatient DICOM tag.
    
    Args:
        orientation: List of 6 floats representing ImageOrientationPatient
    
    Returns:
        str: 'axial', 'sagittal', or 'coronal'
    """
    row_vec = np.array(orientation[:3])
    col_vec = np.array(orientation[3:])
    normal = np.cross(row_vec, col_vec)
    abs_normal = np.abs(normal)
    
    dominant_axis = np.argmax(abs_normal)
    
    if dominant_axis == 2:
        return 'axial'
    elif dominant_axis == 0:
        return 'coronal'
    elif dominant_axis == 1:
        return 'sagittal'


def parse_orientation(value):
    """
    Acepta tanto string "1\\0\\0\\0\\0\\-1" como lista [1, 0, 0, 0, 0, -1].
    """
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split('\\')
    elif isinstance(value, list):
        parts = value
    else:
        return None

    if len(parts) != 6:
        return None

    try:
        return [float(v) for v in parts]
    except (ValueError, TypeError):
        return None


def parse_position(value):
    """
    Acepta tanto string "x\\y\\z" como lista [x, y, z].
    """
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split('\\')
    elif isinstance(value, list):
        parts = value
    else:
        return None

    if len(parts) != 3:
        return None

    try:
        return [float(v) for v in parts]
    except (ValueError, TypeError):
        return None


def parse_instance_number(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None


def parse_series_number(value):
    if value in (None, ''):
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return 0


def compute_slice_position(orientation, position):
    """
    Calcula coordenada escalar del corte proyectando la posicion sobre la normal.
    """
    if orientation is None or position is None:
        return None
    try:
        row_vec = np.array(orientation[:3])
        col_vec = np.array(orientation[3:])
        normal = np.cross(row_vec, col_vec)
        return float(np.dot(np.array(position), normal))
    except Exception:
        return None


def parse_pixel_spacing(value):
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


def parse_pixel_spacing_from_tags(tags):
    if not isinstance(tags, dict):
        return None
    return (
        parse_pixel_spacing(tags.get('PixelSpacing'))
        or parse_pixel_spacing(tags.get('ImagerPixelSpacing'))
    )


def fetch_instance_pixel_spacing(instance_id, auth, base, cache_dict):
    if instance_id in cache_dict:
        return cache_dict[instance_id]

    try:
        response = requests.get(
            f"{base}/instances/{instance_id}/simplified-tags",
            auth=auth,
            timeout=15,
        )
        if response.status_code != 200:
            cache_dict[instance_id] = None
            return None
        tags = response.json()
    except Exception:
        cache_dict[instance_id] = None
        return None

    cache_dict[instance_id] = parse_pixel_spacing_from_tags(tags)
    return cache_dict[instance_id]


def fetch_series_pixel_spacing(series_id, auth, base, cache_dict):
    if series_id in cache_dict:
        return cache_dict[series_id]

    try:
        response = requests.get(
            f"{base}/series/{series_id}/shared-tags",
            auth=auth,
            timeout=15,
        )
        if response.status_code != 200:
            cache_dict[series_id] = None
            return None
        tags = response.json()
    except Exception:
        cache_dict[series_id] = None
        return None

    cache_dict[series_id] = parse_pixel_spacing_from_tags(tags)
    return cache_dict[series_id]


def fetch_series_tags(series_id, auth, base):
    """
    Fetch simplified tags for all DICOM instances in a series.
    
    Args:
        series_id: Orthanc series ID
        auth: Tuple of (username, password) for basic auth
        base: Base URL for Orthanc
    
    Returns:
        Tuple of (series_id, tags_dict or None)
        tags_dict is { instance_id: { tags } }
    """
    try:
        url = f"{base}/series/{series_id}/instances"
        response = requests.get(url, auth=auth, timeout=30)
        if response.status_code == 200:
            instances = response.json()
            tags_dict = {}
            for instance in instances:
                instance_id = instance.get('ID')
                if instance_id:
                    tags = instance.get('MainDicomTags', {})
                    if not isinstance(tags, dict):
                        tags = {}
                    tags_dict[instance_id] = tags
            return series_id, tags_dict if tags_dict else None
        else:
            return series_id, None
    except Exception:
        return series_id, None


def fetch_series_number(series_id, auth, base, cache_dict):
    if series_id in cache_dict:
        return cache_dict[series_id]

    try:
        response = requests.get(f"{base}/series/{series_id}", auth=auth, timeout=15)
        if response.status_code != 200:
            cache_dict[series_id] = 0
            return 0

        series_data = response.json()
    except Exception:
        cache_dict[series_id] = 0
        return 0

    tags = series_data.get('MainDicomTags', {})
    if not isinstance(tags, dict):
        tags = {}

    series_number = parse_series_number(tags.get('SeriesNumber'))
    cache_dict[series_id] = series_number
    return series_number


def _build_instance_record(instance_id, series_id, tags, base):
    orientation = parse_orientation(tags.get('ImageOrientationPatient'))
    if orientation is None:
        return None

    try:
        plane = classify_plane(orientation)
    except Exception:
        return None

    return {
        'instanceId': instance_id,
        'seriesId': series_id,
        'url': f"{base}/instances/{instance_id}/preview",
        'instanceNumber': parse_instance_number(tags.get('InstanceNumber')),
        'pixelSpacing': parse_pixel_spacing_from_tags(tags),
        '_slicePosition': compute_slice_position(
            orientation,
            parse_position(tags.get('ImagePositionPatient')),
        ),
        'plane': plane,
    }


def _append_missing_series(series_results, series_id):
    for plane in PLANES:
        series_results[plane].setdefault(series_id, [])


def _sort_series_instances(series_instances):
    has_slice_position = any(
        item.get('_slicePosition') is not None
        for item in series_instances
    )
    if has_slice_position:
        series_instances.sort(
            key=lambda x: (
                0 if x.get('_slicePosition') is not None else 1,
                x.get('_slicePosition') if x.get('_slicePosition') is not None else float('inf'),
                x.get('instanceNumber') if x.get('instanceNumber') is not None else float('inf'),
                x.get('instanceId'),
            )
        )
    else:
        series_instances.sort(
            key=lambda x: (
                x.get('instanceNumber') if x.get('instanceNumber') is not None else float('inf'),
                x.get('instanceId'),
            )
        )


def _select_primary_series_instances(instances):
    series_stats = {}

    for index, item in enumerate(instances):
        series_id = item.get('seriesId')
        if not series_id:
            continue

        stats = series_stats.setdefault(
            series_id,
            {
                'count': 0,
                'first_index': index,
            },
        )
        stats['count'] += 1
        if index < stats['first_index']:
            stats['first_index'] = index

    if not series_stats:
        return instances, None

    selected_series_id, _ = min(
        series_stats.items(),
        key=lambda kv: (-kv[1]['count'], kv[1]['first_index'], kv[0]),
    )

    return [item for item in instances if item.get('seriesId') == selected_series_id], selected_series_id


def _select_series_instances_by_rank(instances, rank=0):
    series_stats = {}

    for index, item in enumerate(instances):
        series_id = item.get('seriesId')
        if not series_id:
            continue

        stats = series_stats.setdefault(
            series_id,
            {
                'count': 0,
                'first_index': index,
            },
        )
        stats['count'] += 1
        if index < stats['first_index']:
            stats['first_index'] = index

    if not series_stats:
        return instances, None

    ranked_series = sorted(
        series_stats.items(),
        key=lambda kv: (-kv[1]['count'], kv[1]['first_index'], kv[0]),
    )
    ranked_index = min(max(rank, 0), len(ranked_series) - 1)
    selected_series_id = ranked_series[ranked_index][0]

    return [item for item in instances if item.get('seriesId') == selected_series_id], selected_series_id


def _normalize_pixel_spacing(spacing, decimals=6):
    if not spacing or len(spacing) != 2:
        return None
    return (round(float(spacing[0]), decimals), round(float(spacing[1]), decimals))


def _compute_general_pixel_spacing_and_compact(planes):
    normalized_values = []

    for plane_data in planes.values():
        for instance in plane_data.get('instances', []):
            normalized = _normalize_pixel_spacing(instance.get('pixelSpacing'))
            if normalized is not None:
                normalized_values.append(normalized)
            instance.pop('pixelSpacing', None)

    if not normalized_values:
        return None

    most_common_spacing, _ = Counter(normalized_values).most_common(1)[0]
    return [most_common_spacing[0], most_common_spacing[1]]


def _build_study_index_from_orthanc(orthanc_study_id, base, auth):
    study_url = f"{base}/studies/{orthanc_study_id}"
    try:
        study_response = requests.get(study_url, auth=auth, timeout=15)
    except requests.exceptions.Timeout:
        return None, 504
    except requests.exceptions.ConnectionError:
        return None, 503
    except requests.exceptions.RequestException:
        return None, 502

    if study_response.status_code == 404:
        return None, 404
    if study_response.status_code != 200:
        return None, 502

    try:
        study_data = study_response.json()
    except ValueError:
        return None, 502

    series_ids = study_data.get('Series', [])
    if not isinstance(series_ids, list):
        series_ids = []
    series_ids = [sid for sid in series_ids if isinstance(sid, str) and sid]
    known_series_ids = set(series_ids)

    series_results = {
        plane: {series_id: [] for series_id in series_ids}
        for plane in PLANES
    }
    classified_count = 0
    instance_pixel_spacing_cache = {}
    series_pixel_spacing_cache = {}
    series_number_cache = {}
    instances_url = f"{base}/studies/{orthanc_study_id}/instances"
    try:
        instances_response = requests.get(instances_url, auth=auth, timeout=30)
        instances_payload = instances_response.json() if instances_response.status_code == 200 else []
    except Exception:
        instances_payload = []

    if isinstance(instances_payload, list):
        for instance in instances_payload:
            if not isinstance(instance, dict):
                continue

            instance_id = instance.get('ID')
            series_id = instance.get('ParentSeries')
            tags = instance.get('MainDicomTags', {})
            if not instance_id or not series_id or not isinstance(tags, dict):
                continue

            if series_id not in known_series_ids:
                known_series_ids.add(series_id)
                series_ids.append(series_id)
                _append_missing_series(series_results, series_id)

            if series_id not in series_number_cache:
                series_number_cache[series_id] = parse_series_number(tags.get('SeriesNumber'))

            record = _build_instance_record(instance_id, series_id, tags, base)
            if not record:
                continue

            if record.get('pixelSpacing') is not None:
                series_pixel_spacing_cache.setdefault(series_id, record.get('pixelSpacing'))

            if record.get('pixelSpacing') is None:
                record['pixelSpacing'] = fetch_series_pixel_spacing(
                    series_id,
                    auth,
                    base,
                    series_pixel_spacing_cache,
                )

            if record.get('pixelSpacing') is None:
                record['pixelSpacing'] = fetch_instance_pixel_spacing(
                    instance_id,
                    auth,
                    base,
                    instance_pixel_spacing_cache,
                )
                if record.get('pixelSpacing') is not None:
                    series_pixel_spacing_cache[series_id] = record['pixelSpacing']

            plane = record.pop('plane')
            series_results[plane][series_id].append(record)
            classified_count += 1

    if classified_count == 0 and series_ids:
        series_results = {
            plane: {series_id: [] for series_id in series_ids}
            for plane in PLANES
        }
        with ThreadPoolExecutor(max_workers=_max_workers()) as executor:
            futures = {
                executor.submit(fetch_series_tags, sid, auth, base): sid
                for sid in series_ids
            }
            for future in as_completed(futures):
                series_id, series_tags = future.result()
                if not series_tags:
                    continue
                for instance_id, tags in series_tags.items():
                    record = _build_instance_record(instance_id, series_id, tags, base)
                    if not record:
                        continue

                    if record.get('pixelSpacing') is not None:
                        series_pixel_spacing_cache.setdefault(series_id, record.get('pixelSpacing'))

                    if record.get('pixelSpacing') is None:
                        record['pixelSpacing'] = fetch_series_pixel_spacing(
                            series_id,
                            auth,
                            base,
                            series_pixel_spacing_cache,
                        )

                    if record.get('pixelSpacing') is None:
                        record['pixelSpacing'] = fetch_instance_pixel_spacing(
                            instance_id,
                            auth,
                            base,
                            instance_pixel_spacing_cache,
                        )
                        if record.get('pixelSpacing') is not None:
                            series_pixel_spacing_cache[series_id] = record['pixelSpacing']

                    plane = record.pop('plane')
                    series_results[plane][series_id].append(record)

    series_order = []
    for series_id in series_ids:
        number = fetch_series_number(series_id, auth, base, series_number_cache)
        series_order.append((number, series_id))
    series_order.sort(key=lambda item: (item[0], item[1]))
    sorted_series_ids = [series_id for _, series_id in series_order]

    planes = {}
    total_instances = 0
    for plane in PLANES:
        instances = []
        for series_id in sorted_series_ids:
            series_instances = series_results[plane].get(series_id, [])
            if not series_instances:
                continue

            _sort_series_instances(series_instances)
            for item in series_instances:
                item.pop('_slicePosition', None)
                instances.append(item)

        planes[plane] = {
            'total': len(instances),
            'instances': instances,
        }
        total_instances += len(instances)

    general_pixel_spacing = _compute_general_pixel_spacing_and_compact(planes)

    return {
        'orthancStudyId': orthanc_study_id,
        'seriesCount': len(sorted_series_ids),
        'total': total_instances,
        'pixelSpacing': general_pixel_spacing,
        'planes': planes,
    }, 200


def _get_study_index(orthanc_study_id, force_refresh=False):
    cache_key = _study_cache_key(orthanc_study_id)
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if isinstance(cached_data, dict):
            return cached_data, True, 200

    base = settings.ORTHANC_URL
    auth = (settings.ORTHANC_USER, settings.ORTHANC_PASS)
    index_data, status_code = _build_study_index_from_orthanc(orthanc_study_id, base, auth)

    if status_code != 200 or not index_data:
        return None, False, status_code

    cache.set(cache_key, index_data, _cache_ttl_seconds())
    return index_data, False, 200


class StudyImagesIndexView(APIView):
    """
    Returns all study instances grouped by plane in a single response.
    """
    renderer_classes = [JSONRenderer]

    def get(self, request, orthanc_study_id):
        force_refresh = _is_truthy(request.query_params.get('refresh'))
        index_data, cache_hit, status_code = _get_study_index(
            orthanc_study_id,
            force_refresh=force_refresh,
        )

        if status_code == 404:
            return Response({'error': 'Study not found in Orthanc'}, status=404)
        if status_code == 504:
            return Response({'error': 'Orthanc timeout'}, status=504)
        if status_code == 503:
            return Response({'error': 'Orthanc unreachable'}, status=503)
        if status_code != 200 or not index_data:
            return Response({'error': 'Orthanc request failed'}, status=502)

        payload = {
            **index_data,
            'cacheHit': cache_hit,
        }
        return Response(payload, status=200)


class BaseStudyPlaneView(APIView):
    """
    Base class for filtering DICOM instances by plane orientation.
    """
    renderer_classes = [JSONRenderer]
    plane = None
    
    def get(self, request, orthanc_study_id):
        force_refresh = _is_truthy(request.query_params.get('refresh'))
        primary_only = _is_truthy(request.query_params.get('primaryOnly', 'true'))
        index_data, cache_hit, status_code = _get_study_index(
            orthanc_study_id,
            force_refresh=force_refresh,
        )

        if status_code == 404:
            return Response({'error': 'Study not found in Orthanc'}, status=404)
        if status_code == 504:
            return Response({'error': 'Orthanc timeout'}, status=504)
        if status_code == 503:
            return Response({'error': 'Orthanc unreachable'}, status=503)
        if status_code != 200 or not index_data:
            return Response({'error': 'Orthanc request failed'}, status=502)

        plane_data = index_data.get('planes', {}).get(self.plane, {'total': 0, 'instances': []})
        instances = plane_data.get('instances', [])
        if primary_only and instances:
            series_rank = 1 if self.plane == 'axial' else 0
            instances, _ = _select_series_instances_by_rank(instances, series_rank)

        return Response(
            {
                'orthancStudyId': orthanc_study_id,
                'plane': self.plane,
                'total': len(instances) if primary_only else plane_data.get('total', 0),
                'pixelSpacing': index_data.get('pixelSpacing'),
                'instances': instances,
                'cacheHit': cache_hit,
                'primaryOnly': primary_only,
            },
            status=200,
        )


class StudyAxialView(BaseStudyPlaneView):
    """
    Retrieve DICOM instances from a study filtered by axial plane.
    """
    plane = 'axial'


class StudySagittalView(BaseStudyPlaneView):
    """
    Retrieve DICOM instances from a study filtered by sagittal plane.
    """
    plane = 'sagittal'


class StudyCoronalView(BaseStudyPlaneView):
    """
    Retrieve DICOM instances from a study filtered by coronal plane.
    """
    plane = 'coronal'


class StudyDebugView(APIView):
    """
    Temporary debug endpoint to inspect DICOM series and instance tags.
    """

    def get(self, request, orthanc_study_id):
        base = settings.ORTHANC_URL
        auth = (settings.ORTHANC_USER, settings.ORTHANC_PASS)

        study_url = f"{base}/studies/{orthanc_study_id}"
        study_response = requests.get(study_url, auth=auth, timeout=15)
        study_data = study_response.json()

        series_ids = study_data.get('Series', [])

        debug = []

        for series_id in series_ids:
            series_tags_url = f"{base}/series/{series_id}/instances"
            series_response = requests.get(series_tags_url, auth=auth, timeout=30)
            instances = series_response.json()
            if not isinstance(instances, list) or not instances:
                continue

            first_instance = instances[0]
            first_instance_id = first_instance.get('ID')
            if not first_instance_id:
                continue

            first_tags = first_instance.get('MainDicomTags', {})

            debug_entry = {
                'seriesId': series_id,
                'firstInstanceId': first_instance_id,
                'ImageOrientationPatient': first_tags.get('ImageOrientationPatient'),
                'ImageType': first_tags.get('ImageType'),
                'Modality': first_tags.get('Modality'),
                'allTagKeys': list(first_tags.keys()),
            }

            debug.append(debug_entry)

        return Response(debug, status=200)
