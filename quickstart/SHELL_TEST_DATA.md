# Seed de datos de prueba para Django shell

## 1) Abrir la shell

```powershell
c:/Users/Alfredo/Desktop/VisumedDjango/venv/Scripts/python.exe .\manage.py shell
```

## 2) Crear rapido un doctor y un paciente (nuevo esquema por carpetas)

```python
from orthanc.clinical.models import Doctor, Patient

doctor = Doctor.objects.create(
    firstName="Diego",
    lastName="Herrera",
    email="diego.herrera@visumed.test",
    phone="+52-555-300-0001",
    role="referring",
    passwordHash="pbkdf2_sha256$260000$quickhash"
)

patient = Patient.objects.create(
    firstName="Sofia",
    lastName="Navarro",
    email="sofia.navarro@testmail.com",
    phone="+52-555-300-0002",
    gender="female"
)

print("Doctor creado:", doctor.id, doctor.firstName, doctor.lastName)
print("Paciente creado:", patient.id, patient.firstName, patient.lastName)
```

## 3) Seed completo (doctores, pacientes, studies y reports)

```python
from datetime import date, datetime
from django.utils import timezone
from orthanc.clinical.models import Doctor, Patient, Study, Report

# OPCIONAL: limpiar datos anteriores (respeta orden por dependencias)
Report.objects.all().delete()
Study.objects.all().delete()
Patient.objects.all().delete()
Doctor.objects.all().delete()

# Doctors
admin_doc = Doctor.objects.create(
    firstName="Laura",
    lastName="Martinez",
    email="laura.admin@visumed.test",
    phone="+52-555-100-0001",
    role="admin",
    passwordHash="pbkdf2_sha256$260000$adminhash"
)

radiologist_doc = Doctor.objects.create(
    firstName="Carlos",
    lastName="Ramos",
    email="carlos.radiologist@visumed.test",
    phone="+52-555-100-0002",
    role="radiologist",
    passwordHash="pbkdf2_sha256$260000$radiohash"
)

referring_doc = Doctor.objects.create(
    firstName="Ana",
    lastName="Lopez",
    email="ana.referring@visumed.test",
    phone="+52-555-100-0003",
    role="referring",
    passwordHash="pbkdf2_sha256$260000$refhash"
)

# Patients
patient_1 = Patient.objects.create(
    firstName="Juan",
    lastName="Perez",
    email="juan.perez@testmail.com",
    phone="+52-555-200-0001",
    birthDate=date(1987, 5, 14),
    gender="male",
    address="Av. Reforma 123",
    postalCode="06000",
    state="CDMX"
)

patient_2 = Patient.objects.create(
    firstName="Maria",
    lastName="Gonzalez",
    email="maria.gonzalez@testmail.com",
    phone="+52-555-200-0002",
    birthDate=date(1992, 11, 2),
    gender="female",
    address="Calle Naranjo 45",
    postalCode="44100",
    state="Jalisco"
)

# Studies (A Patient can have many Studies)
study_1 = Study.objects.create(
    orthancStudyId="ORTHANC-STUDY-0001",
    patient=patient_1,
    referringDoctor=referring_doc,
    interpretingDoctor=radiologist_doc,
    modality="CT",
    bodyPart="Chest",
    studyDate=timezone.now(),
    status="pending"
)

study_2 = Study.objects.create(
    orthancStudyId="ORTHANC-STUDY-0002",
    patient=patient_1,
    referringDoctor=referring_doc,
    interpretingDoctor=radiologist_doc,
    modality="MRI",
    bodyPart="Brain",
    studyDate=timezone.now(),
    status="in_progress"
)

study_3 = Study.objects.create(
    orthancStudyId="ORTHANC-STUDY-0003",
    patient=patient_2,
    referringDoctor=admin_doc,
    interpretingDoctor=radiologist_doc,
    modality="US",
    bodyPart="Abdomen",
    studyDate=timezone.now(),
    status="completed"
)

# Reports (A Study can have many Reports)
report_1 = Report.objects.create(
    study=study_1,
    doctor=radiologist_doc,
    studyName="CT Chest",
    technique="Helical CT with contrast",
    studyDate=date.today(),
    indication="Persistent cough",
    findings="Mild bilateral basal infiltrates.",
    priorStudies="No prior studies available.",
    conclusions="Compatible with mild inflammatory process.",
    suggestions="Clinical follow-up and repeat imaging if symptoms persist.",
    status="draft"
)

report_2 = Report.objects.create(
    study=study_1,
    doctor=radiologist_doc,
    studyName="CT Chest Addendum",
    technique="Addendum review",
    studyDate=date.today(),
    indication="Additional review requested",
    findings="No pleural effusion.",
    priorStudies="Compared with same-day CT.",
    conclusions="No additional acute findings.",
    suggestions="Routine follow-up.",
    status="amended"
)

report_3 = Report.objects.create(
    study=study_2,
    doctor=radiologist_doc,
    studyName="MRI Brain",
    technique="Multiplanar, multisequence MRI",
    studyDate=date.today(),
    indication="Headache",
    findings="No focal lesion detected.",
    priorStudies="MRI from 2024 showed no abnormalities.",
    conclusions="Unremarkable MRI brain.",
    suggestions="Neurology evaluation if symptoms continue.",
    status="signed"
)

print("Datos de prueba creados correctamente")
print("Doctors:", Doctor.objects.count())
print("Patients:", Patient.objects.count())
print("Studies:", Study.objects.count())
print("Reports:", Report.objects.count())

# Verificación rápida de relaciones
print("Studies de Juan:", patient_1.studies.count())
print("Reports del study_1:", study_1.reports.count())
print("Studies referidos por Ana:", referring_doc.referred_studies.count())
print("Studies interpretados por Carlos:", radiologist_doc.interpreted_studies.count())
print("Reports firmados por Carlos:", radiologist_doc.reports.count())
```

## 4) Salir de la shell

```python
exit()
```
