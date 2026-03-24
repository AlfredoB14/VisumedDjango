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
]
