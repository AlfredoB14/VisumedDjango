import json
from datetime import date, datetime

import requests
from django.conf import settings
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Doctor, Patient, Report, Study
from .serializers import DoctorSerializer, PatientSerializer, ReportSerializer, StudySerializer


def _parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError('Invalid date format. Expected YYYY-MM-DD')


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)
    raise ValueError('Invalid datetime format. Expected ISO 8601')


def _ensure_password_hash(value):
    if not value:
        return value
    try:
        identify_hasher(value)
        return value
    except ValueError:
        return make_password(value)


def _is_valid_password(raw_password, stored_value):
    if not raw_password or not stored_value:
        return False
    try:
        identify_hasher(stored_value)
        return check_password(raw_password, stored_value)
    except ValueError:
        return raw_password == stored_value


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def doctors_collection(request):
    if request.method == 'GET':
        doctors = Doctor.objects.all().order_by('-createdAt')
        return JsonResponse([DoctorSerializer.serialize(item) for item in doctors], safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    required_fields = ['firstName', 'lastName', 'email', 'role', 'passwordHash']
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return JsonResponse({'error': f"Missing required fields: {', '.join(missing)}"}, status=400)

    try:
        doctor = Doctor.objects.create(
            firstName=payload['firstName'],
            lastName=payload['lastName'],
            email=payload['email'],
            phone=payload.get('phone', ''),
            role=payload['role'],
            passwordHash=_ensure_password_hash(payload['passwordHash']),
        )
        return JsonResponse(DoctorSerializer.serialize(doctor), status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def doctor_detail(request, doctor_id):
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(DoctorSerializer.serialize(doctor))

    if request.method == 'DELETE':
        doctor.delete()
        return JsonResponse({}, status=204)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    for field in ['firstName', 'lastName', 'email', 'phone', 'role', 'passwordHash']:
        if field in payload:
            if field == 'passwordHash':
                setattr(doctor, field, _ensure_password_hash(payload[field]))
            else:
                setattr(doctor, field, payload[field])

    try:
        doctor.save()
        return JsonResponse(DoctorSerializer.serialize(doctor))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def doctor_login(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    email = payload.get('email')
    password = payload.get('password')

    if not email or not password:
        return JsonResponse({'error': 'email and password are required'}, status=400)

    try:
        doctor = Doctor.objects.get(email=email)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    if not _is_valid_password(password, doctor.passwordHash):
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    return JsonResponse(
        {
            'message': 'Login successful',
            'doctor': {
                'id': str(doctor.pk),
                'firstName': doctor.firstName,
                'lastName': doctor.lastName,
                'email': doctor.email,
                'phone': doctor.phone,
                'role': doctor.role,
                'createdAt': doctor.createdAt.isoformat() if doctor.createdAt else None,
            },
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def patients_collection(request):
    if request.method == 'GET':
        patients = Patient.objects.all().order_by('-createdAt')
        return JsonResponse([PatientSerializer.serialize(item) for item in patients], safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    required_fields = ['firstName', 'lastName']
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return JsonResponse({'error': f"Missing required fields: {', '.join(missing)}"}, status=400)

    try:
        patient = Patient.objects.create(
            firstName=payload['firstName'],
            lastName=payload['lastName'],
            email=payload.get('email', ''),
            phone=payload.get('phone', ''),
            birthDate=_parse_date(payload.get('birthDate')),
            gender=payload.get('gender', ''),
            address=payload.get('address', ''),
            postalCode=payload.get('postalCode', ''),
            state=payload.get('state', ''),
        )
        return JsonResponse(PatientSerializer.serialize(patient), status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def patient_detail(request, patient_id):
    try:
        patient = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(PatientSerializer.serialize(patient))

    if request.method == 'DELETE':
        patient.delete()
        return JsonResponse({}, status=204)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    for field in ['firstName', 'lastName', 'email', 'phone', 'gender', 'address', 'postalCode', 'state']:
        if field in payload:
            setattr(patient, field, payload[field])

    if 'birthDate' in payload:
        try:
            patient.birthDate = _parse_date(payload.get('birthDate'))
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

    try:
        patient.save()
        return JsonResponse(PatientSerializer.serialize(patient))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def studies_collection(request):
    if request.method == 'GET':
        studies = Study.objects.select_related('patient', 'referringDoctor', 'interpretingDoctor').all().order_by('-createdAt')
        return JsonResponse([StudySerializer.serialize(item) for item in studies], safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    required_fields = ['orthancStudyId', 'patientId']
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return JsonResponse({'error': f"Missing required fields: {', '.join(missing)}"}, status=400)

    try:
        patient = Patient.objects.get(pk=payload['patientId'])
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    referring_doctor = None
    if payload.get('referringDoctorId'):
        try:
            referring_doctor = Doctor.objects.get(pk=payload['referringDoctorId'])
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Referring doctor not found'}, status=404)

    interpreting_doctor = None
    if payload.get('interpretingDoctorId'):
        try:
            interpreting_doctor = Doctor.objects.get(pk=payload['interpretingDoctorId'])
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Interpreting doctor not found'}, status=404)

    try:
        study = Study.objects.create(
            orthancStudyId=payload['orthancStudyId'],
            patient=patient,
            referringDoctor=referring_doctor,
            interpretingDoctor=interpreting_doctor,
            modality=payload.get('modality', ''),
            bodyPart=payload.get('bodyPart', ''),
            studyDate=_parse_datetime(payload.get('studyDate')),
            status=payload.get('status', Study.STATUS_PENDING),
        )
        return JsonResponse(StudySerializer.serialize(study), status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def study_detail(request, study_id):
    try:
        study = Study.objects.get(pk=study_id)
    except Study.DoesNotExist:
        return JsonResponse({'error': 'Study not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(StudySerializer.serialize(study))

    if request.method == 'DELETE':
        study.delete()
        return JsonResponse({}, status=204)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    if 'orthancStudyId' in payload:
        study.orthancStudyId = payload['orthancStudyId']
    if 'modality' in payload:
        study.modality = payload['modality']
    if 'bodyPart' in payload:
        study.bodyPart = payload['bodyPart']
    if 'status' in payload:
        study.status = payload['status']

    if 'patientId' in payload:
        try:
            study.patient = Patient.objects.get(pk=payload['patientId'])
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)

    if 'referringDoctorId' in payload:
        if payload['referringDoctorId']:
            try:
                study.referringDoctor = Doctor.objects.get(pk=payload['referringDoctorId'])
            except Doctor.DoesNotExist:
                return JsonResponse({'error': 'Referring doctor not found'}, status=404)
        else:
            study.referringDoctor = None

    if 'interpretingDoctorId' in payload:
        if payload['interpretingDoctorId']:
            try:
                study.interpretingDoctor = Doctor.objects.get(pk=payload['interpretingDoctorId'])
            except Doctor.DoesNotExist:
                return JsonResponse({'error': 'Interpreting doctor not found'}, status=404)
        else:
            study.interpretingDoctor = None

    if 'studyDate' in payload:
        try:
            study.studyDate = _parse_datetime(payload.get('studyDate'))
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

    try:
        study.save()
        return JsonResponse(StudySerializer.serialize(study))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def reports_collection(request):
    if request.method == 'GET':
        reports = Report.objects.select_related('study', 'doctor').all().order_by('-createdAt')
        return JsonResponse([ReportSerializer.serialize(item) for item in reports], safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    required_fields = ['studyId']
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return JsonResponse({'error': f"Missing required fields: {', '.join(missing)}"}, status=400)

    try:
        study = Study.objects.get(pk=payload['studyId'])
    except Study.DoesNotExist:
        return JsonResponse({'error': 'Study not found'}, status=404)

    doctor = None
    if payload.get('doctorId'):
        try:
            doctor = Doctor.objects.get(pk=payload['doctorId'])
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctor not found'}, status=404)

    try:
        report = Report.objects.create(
            study=study,
            doctor=doctor,
            studyName=payload.get('studyName', ''),
            technique=payload.get('technique', ''),
            studyDate=_parse_date(payload.get('studyDate')),
            indication=payload.get('indication', ''),
            findings=payload.get('findings', ''),
            priorStudies=payload.get('priorStudies', ''),
            conclusions=payload.get('conclusions', ''),
            suggestions=payload.get('suggestions', ''),
            status=payload.get('status', Report.STATUS_DRAFT),
        )
        return JsonResponse(ReportSerializer.serialize(report), status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def report_detail(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(ReportSerializer.serialize(report))

    if request.method == 'DELETE':
        report.delete()
        return JsonResponse({}, status=204)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    for field in ['studyName', 'technique', 'indication', 'findings', 'priorStudies', 'conclusions', 'suggestions', 'status']:
        if field in payload:
            setattr(report, field, payload[field])

    if 'studyId' in payload:
        try:
            report.study = Study.objects.get(pk=payload['studyId'])
        except Study.DoesNotExist:
            return JsonResponse({'error': 'Study not found'}, status=404)

    if 'doctorId' in payload:
        if payload['doctorId']:
            try:
                report.doctor = Doctor.objects.get(pk=payload['doctorId'])
            except Doctor.DoesNotExist:
                return JsonResponse({'error': 'Doctor not found'}, status=404)
        else:
            report.doctor = None

    if 'studyDate' in payload:
        try:
            report.studyDate = _parse_date(payload.get('studyDate'))
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

    try:
        report.save()
        return JsonResponse(ReportSerializer.serialize(report))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class StudyUploadView(View):
    def post(self, request):
        dicom_file = request.FILES.get('dicom_file')
        patient_id = request.POST.get('patient_id')
        referring_doctor_id = request.POST.get('referring_doctor_id')

        if not dicom_file:
            return JsonResponse({'error': 'dicom_file is required'}, status=400)

        if not patient_id:
            return JsonResponse({'error': 'patient_id is required'}, status=400)

        if not referring_doctor_id:
            return JsonResponse({'error': 'referring_doctor_id is required'}, status=400)

        try:
            orthanc_response = requests.post(
                f"{settings.ORTHANC_URL}/instances",
                data=dicom_file.read(),
                headers={'Content-Type': 'application/dicom'},
                timeout=30,
            )
        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'Orthanc timeout'}, status=504)
        except requests.exceptions.ConnectionError:
            return JsonResponse({'error': 'Orthanc unreachable'}, status=503)

        if orthanc_response.status_code != 200:
            return JsonResponse(
                {'error': 'Orthanc upload failed', 'detail': orthanc_response.text},
                status=502,
            )

        try:
            orthanc_payload = orthanc_response.json()
            parent_study = orthanc_payload.get('ParentStudy')
        except ValueError:
            return JsonResponse({'error': 'Orthanc upload failed', 'detail': 'Invalid Orthanc response'}, status=502)

        if not parent_study:
            return JsonResponse({'error': 'Orthanc upload failed', 'detail': 'ParentStudy missing in Orthanc response'}, status=502)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)

        try:
            referring_doctor = Doctor.objects.get(pk=referring_doctor_id)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Referring doctor not found'}, status=404)

        study = Study.objects.create(
            orthancStudyId=parent_study,
            patient=patient,
            referringDoctor=referring_doctor,
            status=Study.STATUS_PENDING,
        )

        return JsonResponse(StudySerializer.serialize(study), status=201)
