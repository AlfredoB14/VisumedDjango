from flask import Flask, jsonify, Response, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir solicitudes desde el frontend

# Configuración de Orthanc
ORTHANC_URL = "https://orthancpinguland-production.up.railway.app"  # Cambia esto a la URL de tu servidor Orthanc

# Función para realizar solicitudes a Orthanc
def orthanc_request(path, method="GET", data=None, params=None):
    url = f"{ORTHANC_URL}{path}"
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a Orthanc: {e}")
        return None

@app.route('/api/studies/<study_id>/images', methods=['GET'])
def get_study_images(study_id):
    try:
        quality = request.args.get('quality', 25, type=int)
        
        # Obtener lista de instancias del estudio con detalles
        response = orthanc_request(f"/studies/{study_id}/instances")
        if not response:
            return jsonify({"error": "No se pudo obtener las instancias del estudio"}), 500
        
        instances = response.json()
        
        # Obtener todos los IDs de series únicos presentes en el estudio
        series_ids = {instance["ParentSeries"] for instance in instances}
        
        # Mapear cada serie a su SeriesNumber
        series_numbers = {}
        for series_id in series_ids:
            series_response = orthanc_request(f"/series/{series_id}")
            if series_response:
                series_data = series_response.json()
                series_number_str = series_data.get('MainDicomTags', {}).get('SeriesNumber', '0')
                try:
                    series_numbers[series_id] = int(series_number_str)
                except ValueError:
                    series_numbers[series_id] = 0  # Valor por defecto si hay error
        
        # Preparar lista de instancias con sus números de serie e instancia
        instances_with_numbers = []
        for instance in instances:
            instance_info = {
                "id": instance["ID"],
                "series_id": instance["ParentSeries"],
                "series_number": series_numbers.get(instance["ParentSeries"], 0),
                "instance_number": int(instance.get('MainDicomTags', {}).get('InstanceNumber', '0') or '0')
            }
            instances_with_numbers.append(instance_info)
        
        # Ordenar primero por SeriesNumber y luego por InstanceNumber
        sorted_instances = sorted(
            instances_with_numbers,
            key=lambda x: (x["series_number"], x["instance_number"])
        )
        
        # Generar URLs en el orden correcto
        image_urls = []
        for instance in sorted_instances:
            image_url = f"{ORTHANC_URL}/instances/{instance['id']}/frames/0/rendered?quality={quality}"
            image_urls.append({
                "instanceId": instance['id'],
                "imageUrl": image_url,
                "seriesNumber": instance["series_number"],
                "instanceNumber": instance["instance_number"]
            })
        
        return jsonify({
            "studyId": study_id,
            "imageCount": len(image_urls),
            "images": image_urls
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para obtener una imagen renderizada específica
@app.route('/api/instances/<instance_id>/rendered', methods=['GET'])
def get_rendered_instance(instance_id):
    try:
        # Obtener calidad deseada para la imagen
        quality = request.args.get('quality', 90, type=int)
        
        # Obtener la imagen renderizada de Orthanc
        response = orthanc_request(f"/instances/{instance_id}/rendered", params={"quality": quality})
        if not response:
            return jsonify({"error": "No se pudo obtener la imagen"}), 500
        
        # Devolver la imagen como respuesta binaria
        return Response(
            response.content,
            mimetype="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=instance-{instance_id}.jpg",
                "Cache-Control": "public, max-age=86400"  # Caché por 24 horas
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint adicional para obtener metadatos del estudio
@app.route('/api/studies/<study_id>/metadata', methods=['GET'])
def get_study_metadata(study_id):
    try:
        response = orthanc_request(f"/studies/{study_id}")
        if not response:
            return jsonify({"error": "No se pudo obtener los metadatos del estudio"}), 500
        
        # Obtener etiquetas DICOM compartidas para información adicional
        shared_tags_response = orthanc_request(f"/studies/{study_id}/shared-tags")
        shared_tags = shared_tags_response.json() if shared_tags_response else {}
        
        # Extraer información relevante
        metadata = response.json()
        metadata["SharedTags"] = shared_tags
        
        return jsonify(metadata)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para listar todos los estudios disponibles
@app.route('/api/studies', methods=['GET'])
def get_all_studies():
    try:
        response = orthanc_request("/studies")
        if not response:
            return jsonify({"error": "No se pudo obtener la lista de estudios"}), 500
        
        studies = response.json()
        
        # Opcional: Obtener más información para cada estudio
        if request.args.get('expand', 'false').lower() == 'true':
            detailed_studies = []
            for study_id in studies:
                study_info_response = orthanc_request(f"/studies/{study_id}")
                if study_info_response:
                    detailed_studies.append(study_info_response.json())
            return jsonify(detailed_studies)
        
        return jsonify(studies)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)