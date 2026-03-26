import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.conf import settings

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
    'fetch_series_tags',
    'BaseStudyPlaneView',
    'StudyAxialView',
    'StudySagittalView',
    'StudyCoronalView',
    'StudyDebugView',
]


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
        return 'sagittal'
    elif dominant_axis == 1:
        return 'coronal'


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
                    if isinstance(tags, dict):
                        tags['ImageOrientationPatient'] = parse_orientation(
                            tags.get('ImageOrientationPatient')
                        )
                    tags_dict[instance_id] = tags
            return series_id, tags_dict if tags_dict else None
        else:
            return series_id, None
    except Exception:
        return series_id, None


class BaseStudyPlaneView(APIView):
    """
    Base class for filtering DICOM instances by plane orientation.
    """
    renderer_classes = [JSONRenderer]
    plane = None
    
    def get(self, request, orthanc_study_id):
        try:
            base = settings.ORTHANC_URL
            auth = (settings.ORTHANC_USER, settings.ORTHANC_PASS)
            
            study_url = f"{base}/studies/{orthanc_study_id}"
            study_response = requests.get(study_url, auth=auth, timeout=15)
            
            if study_response.status_code != 200:
                return Response(
                    {"error": "Study not found in Orthanc"},
                    status=404
                )
            
            study_data = study_response.json()
            series_ids = study_data.get('Series', [])
            
            results = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(fetch_series_tags, sid, auth, base): sid
                    for sid in series_ids
                }
                for future in as_completed(futures):
                    series_id, series_tags = future.result()
                    if not series_tags:
                        continue
                    
                    for instance_id, tags in series_tags.items():
                        orientation = parse_orientation(tags.get('ImageOrientationPatient'))
                        if orientation is None:
                            continue
                        try:
                            plane = classify_plane(orientation)
                        except Exception:
                            continue
                        
                        if plane == self.plane:
                            results.append({
                                'instanceId': instance_id,
                                'seriesId': series_id,
                                'url': f"{base}/instances/{instance_id}/preview",
                                'instanceNumber': tags.get('InstanceNumber'),
                            })
            
            results.sort(key=lambda x: int(x.get('instanceNumber', 0)) if x.get('instanceNumber') else 0)
            
            return Response(
                {
                    'orthancStudyId': orthanc_study_id,
                    'plane': self.plane,
                    'total': len(results),
                    'instances': results
                },
                status=200
            )
        
        except requests.exceptions.Timeout:
            return Response(
                {"error": "Orthanc timeout"},
                status=504
            )
        except requests.exceptions.ConnectionError:
            return Response(
                {"error": "Orthanc unreachable"},
                status=503
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
