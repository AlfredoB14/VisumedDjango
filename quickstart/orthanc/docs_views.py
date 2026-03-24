from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


patient_id_param = openapi.Parameter('patient_id', openapi.IN_PATH, description='Patient ObjectId', type=openapi.TYPE_STRING)
doctor_id_param = openapi.Parameter('doctor_id', openapi.IN_PATH, description='Doctor ObjectId', type=openapi.TYPE_STRING)
study_id_param = openapi.Parameter('study_id', openapi.IN_PATH, description='Study ObjectId or Orthanc study id depending on endpoint', type=openapi.TYPE_STRING)
report_id_param = openapi.Parameter('report_id', openapi.IN_PATH, description='Report ObjectId', type=openapi.TYPE_STRING)
instance_id_param = openapi.Parameter('instance_id', openapi.IN_PATH, description='Orthanc instance id', type=openapi.TYPE_STRING)
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
    operation_description='Create doctor',
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


@swagger_auto_schema(method='get', tags=['Patients'], operation_description='List patients')
@swagger_auto_schema(
    method='post',
    tags=['Patients'],
    operation_description='Create patient',
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


@swagger_auto_schema(method='get', tags=['Studies'], operation_description='List studies from DB')
@swagger_auto_schema(
    method='post',
    tags=['Studies'],
    operation_description='Create study in DB',
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
    operation_description='Create report',
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
