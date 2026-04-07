from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


patient_id_param = openapi.Parameter('patient_id', openapi.IN_PATH, description='Patient ObjectId', type=openapi.TYPE_STRING)
patient_id_query_param = openapi.Parameter('patientId', openapi.IN_QUERY, description='Filter studies by Patient ObjectId', type=openapi.TYPE_STRING, required=False)
doctor_id_param = openapi.Parameter('doctor_id', openapi.IN_PATH, description='Doctor ObjectId', type=openapi.TYPE_STRING)
doctor_id_query_param = openapi.Parameter('doctorId', openapi.IN_QUERY, description='Filter patients by Doctor ObjectId', type=openapi.TYPE_STRING, required=False)
study_id_param = openapi.Parameter('study_id', openapi.IN_PATH, description='Study ObjectId or Orthanc study id depending on endpoint', type=openapi.TYPE_STRING)
report_id_param = openapi.Parameter('report_id', openapi.IN_PATH, description='Report ObjectId', type=openapi.TYPE_STRING)
instance_id_param = openapi.Parameter('instance_id', openapi.IN_PATH, description='Orthanc instance id', type=openapi.TYPE_STRING)
orthanc_study_id_param = openapi.Parameter('orthanc_study_id', openapi.IN_PATH, description='Orthanc study id', type=openapi.TYPE_STRING)
upload_dicom_file_param = openapi.Parameter('dicom_file', openapi.IN_FORM, description='.dcm file', type=openapi.TYPE_FILE, required=True)
upload_patient_id_param = openapi.Parameter('patient_id', openapi.IN_FORM, description='Patient ObjectId', type=openapi.TYPE_STRING, required=True)
upload_referring_doctor_id_param = openapi.Parameter('referring_doctor_id', openapi.IN_FORM, description='Doctor ObjectId', type=openapi.TYPE_STRING, required=True)


@swagger_auto_schema(method='get', tags=['Orthanc'], operation_description='List all studies from Orthanc')
@api_view(['GET'])
def docs_get_all_studies(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[study_id_param], operation_description='Get rendered images of a study from Orthanc')
@api_view(['GET'])
def docs_get_study_images(request, study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[study_id_param], operation_description='Get study metadata from Orthanc')
@api_view(['GET'])
def docs_get_study_metadata(request, study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[orthanc_study_id_param], operation_description='Get axial images from an Orthanc study')
@api_view(['GET'])
def docs_get_study_images_axial(request, orthanc_study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[orthanc_study_id_param], operation_description='Get all study images grouped by plane in one response')
@api_view(['GET'])
def docs_get_study_images_index(request, orthanc_study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[orthanc_study_id_param], operation_description='Get sagittal images from an Orthanc study')
@api_view(['GET'])
def docs_get_study_images_sagittal(request, orthanc_study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[orthanc_study_id_param], operation_description='Get coronal images from an Orthanc study')
@api_view(['GET'])
def docs_get_study_images_coronal(request, orthanc_study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[orthanc_study_id_param], operation_description='Debug Orthanc study series and tags')
@api_view(['GET'])
def docs_get_study_debug(request, orthanc_study_id):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Orthanc'], manual_parameters=[instance_id_param], operation_description='Render a DICOM instance as image')
@api_view(['GET'])
def docs_get_rendered_instance(request, instance_id):
    return Response(status=200)


@swagger_auto_schema(
    method='get',
    tags=['Doctors'],
    operation_description='List doctors',
)
@swagger_auto_schema(
    method='post',
    tags=['Doctors'],
    operation_description='Create doctor. Required: firstName, lastName, email, role, passwordHash. Optional: phone.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['firstName', 'lastName', 'email', 'role', 'passwordHash'],
        properties={
            'firstName': openapi.Schema(type=openapi.TYPE_STRING),
            'lastName': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'phone': openapi.Schema(type=openapi.TYPE_STRING),
            'role': openapi.Schema(type=openapi.TYPE_STRING),
            'passwordHash': openapi.Schema(type=openapi.TYPE_STRING),
        },
        example={
            'firstName': 'Ana',
            'lastName': 'Lopez',
            'email': 'ana@example.com',
            'phone': '+52-555-111-2222',
            'role': 'radiologist',
            'passwordHash': 'plain-or-hashed-password',
        },
    ),
)
@api_view(['GET', 'POST'])
def docs_doctors_collection(request):
    return Response(status=200)


@swagger_auto_schema(
    method='post',
    tags=['Doctors'],
    operation_description='Doctor login by email and password',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
)
@api_view(['POST'])
def docs_doctor_login(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Doctors'], manual_parameters=[doctor_id_param], operation_description='Get doctor by id')
@swagger_auto_schema(method='put', tags=['Doctors'], manual_parameters=[doctor_id_param], operation_description='Update doctor by id')
@swagger_auto_schema(method='delete', tags=['Doctors'], manual_parameters=[doctor_id_param], operation_description='Delete doctor by id')
@api_view(['GET', 'PUT', 'DELETE'])
def docs_doctor_detail(request, doctor_id):
    return Response(status=200)


@swagger_auto_schema(
    method='get',
    tags=['Doctors'],
    manual_parameters=[doctor_id_param],
    operation_description='List patients assigned to a doctor by id',
)
@api_view(['GET'])
def docs_doctor_patients(request, doctor_id):
    return Response(status=200)


@swagger_auto_schema(
    method='get',
    tags=['Patients'],
    manual_parameters=[doctor_id_query_param],
    operation_description='List patients (optional filter by doctorId)',
)
@swagger_auto_schema(
    method='post',
    tags=['Patients'],
    operation_description='Create patient. Required: firstName, lastName. Optional: email, phone, birthDate, gender, address, postalCode, state, doctorId.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['firstName', 'lastName'],
        properties={
            'firstName': openapi.Schema(type=openapi.TYPE_STRING),
            'lastName': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'phone': openapi.Schema(type=openapi.TYPE_STRING),
            'birthDate': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            'gender': openapi.Schema(type=openapi.TYPE_STRING),
            'address': openapi.Schema(type=openapi.TYPE_STRING),
            'postalCode': openapi.Schema(type=openapi.TYPE_STRING),
            'state': openapi.Schema(type=openapi.TYPE_STRING),
            'doctorId': openapi.Schema(type=openapi.TYPE_STRING),
        },
        example={
            'firstName': 'Carlos',
            'lastName': 'Mendez',
            'email': 'carlos@example.com',
            'phone': '+52-555-333-4444',
            'birthDate': '1988-10-21',
            'gender': 'male',
            'address': 'Av. Reforma 123',
            'postalCode': '06600',
            'state': 'CDMX',
            'doctorId': '67f1572f901f73d6f8b0c111',
        },
    ),
)
@api_view(['GET', 'POST'])
def docs_patients_collection(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Patients'], manual_parameters=[patient_id_param], operation_description='Get patient by id')
@swagger_auto_schema(method='put', tags=['Patients'], manual_parameters=[patient_id_param], operation_description='Update patient by id')
@swagger_auto_schema(method='delete', tags=['Patients'], manual_parameters=[patient_id_param], operation_description='Delete patient by id')
@api_view(['GET', 'PUT', 'DELETE'])
def docs_patient_detail(request, patient_id):
    return Response(status=200)


@swagger_auto_schema(
    method='get',
    tags=['Studies'],
    manual_parameters=[patient_id_param],
    operation_description='List studies-db assigned to a patient by id',
)
@api_view(['GET'])
def docs_patient_studies(request, patient_id):
    return Response(status=200)


@swagger_auto_schema(
    method='get',
    tags=['Studies'],
    manual_parameters=[patient_id_query_param],
    operation_description='List studies from DB (optional filter by patientId)',
)
@swagger_auto_schema(
    method='post',
    tags=['Studies'],
    operation_description='Create study in DB. Required: orthancStudyId, patientId. Optional: referringDoctorId, interpretingDoctorId, modality, bodyPart, studyDate, status.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['orthancStudyId', 'patientId'],
        properties={
            'orthancStudyId': openapi.Schema(type=openapi.TYPE_STRING),
            'patientId': openapi.Schema(type=openapi.TYPE_STRING),
            'referringDoctorId': openapi.Schema(type=openapi.TYPE_STRING),
            'interpretingDoctorId': openapi.Schema(type=openapi.TYPE_STRING),
            'modality': openapi.Schema(type=openapi.TYPE_STRING),
            'bodyPart': openapi.Schema(type=openapi.TYPE_STRING),
            'studyDate': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
        },
        example={
            'orthancStudyId': '1.2.840.113619.2.55.3.604688435.123.1711030511.467',
            'patientId': '67f1572f901f73d6f8b0c222',
            'referringDoctorId': '67f1572f901f73d6f8b0c111',
            'interpretingDoctorId': '67f1572f901f73d6f8b0c333',
            'modality': 'CT',
            'bodyPart': 'Chest',
            'studyDate': '2026-04-06T19:30:00Z',
            'status': 'pending',
        },
    ),
)
@api_view(['GET', 'POST'])
def docs_studies_collection(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Studies'], manual_parameters=[study_id_param], operation_description='Get study by id')
@swagger_auto_schema(method='put', tags=['Studies'], manual_parameters=[study_id_param], operation_description='Update study by id')
@swagger_auto_schema(method='delete', tags=['Studies'], manual_parameters=[study_id_param], operation_description='Delete study by id')
@api_view(['GET', 'PUT', 'DELETE'])
def docs_study_detail(request, study_id):
    return Response(status=200)


@swagger_auto_schema(
    method='post',
    tags=['Studies'],
    operation_description='Upload DICOM file to Orthanc and create Study record',
    consumes=['multipart/form-data'],
    manual_parameters=[
        upload_dicom_file_param,
        upload_patient_id_param,
        upload_referring_doctor_id_param,
    ],
)
@api_view(['POST'])
def docs_study_upload(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Reports'], operation_description='List reports')
@swagger_auto_schema(
    method='post',
    tags=['Reports'],
    operation_description='Create report. Required: studyId. Optional: doctorId, studyName, technique, studyDate, indication, findings, priorStudies, conclusions, suggestions, status.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['studyId'],
        properties={
            'studyId': openapi.Schema(type=openapi.TYPE_STRING),
            'doctorId': openapi.Schema(type=openapi.TYPE_STRING),
            'studyName': openapi.Schema(type=openapi.TYPE_STRING),
            'technique': openapi.Schema(type=openapi.TYPE_STRING),
            'studyDate': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            'indication': openapi.Schema(type=openapi.TYPE_STRING),
            'findings': openapi.Schema(type=openapi.TYPE_STRING),
            'priorStudies': openapi.Schema(type=openapi.TYPE_STRING),
            'conclusions': openapi.Schema(type=openapi.TYPE_STRING),
            'suggestions': openapi.Schema(type=openapi.TYPE_STRING),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
        },
        example={
            'studyId': '67f1572f901f73d6f8b0c444',
            'doctorId': '67f1572f901f73d6f8b0c333',
            'studyName': 'CT Chest with contrast',
            'technique': 'Axial 1mm, coronal and sagittal reconstructions',
            'studyDate': '2026-04-06',
            'indication': 'Persistent cough',
            'findings': 'No acute pulmonary process.',
            'priorStudies': 'Comparison with CT from 2025-12-10.',
            'conclusions': 'No acute findings.',
            'suggestions': 'Clinical follow-up.',
            'status': 'draft',
        },
    ),
)
@api_view(['GET', 'POST'])
def docs_reports_collection(request):
    return Response(status=200)


@swagger_auto_schema(method='get', tags=['Reports'], manual_parameters=[report_id_param], operation_description='Get report by id')
@swagger_auto_schema(method='put', tags=['Reports'], manual_parameters=[report_id_param], operation_description='Update report by id')
@swagger_auto_schema(method='delete', tags=['Reports'], manual_parameters=[report_id_param], operation_description='Delete report by id')
@api_view(['GET', 'PUT', 'DELETE'])
def docs_report_detail(request, report_id):
    return Response(status=200)
