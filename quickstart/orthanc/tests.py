import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from orthanc.clinical.models import Consultation, Doctor, Patient, Study


class DoctorPatientsEndpointTests(TestCase):
	def setUp(self):
		self.doctor_1 = Doctor.objects.create(
			firstName='Ana',
			lastName='Lopez',
			email='ana@example.com',
			phone='555-111',
			role=Doctor.ROLE_RADIOLOGIST,
			passwordHash='secret',
		)
		self.doctor_2 = Doctor.objects.create(
			firstName='Luis',
			lastName='Perez',
			email='luis@example.com',
			phone='555-222',
			role=Doctor.ROLE_REFERRING,
			passwordHash='secret',
		)

	def test_create_patient_with_doctor_id_returns_doctor_id(self):
		payload = {
			'firstName': 'Carlos',
			'lastName': 'Mendez',
			'doctorId': str(self.doctor_1.pk),
		}

		response = self.client.post(
			'/api/patients/',
			data=json.dumps(payload),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		data = response.json()
		self.assertEqual(data['doctorId'], str(self.doctor_1.pk))

	def test_doctor_patients_endpoint_returns_only_assigned_patients(self):
		p1 = Patient.objects.create(firstName='A', lastName='One', doctor=self.doctor_1)
		p2 = Patient.objects.create(firstName='B', lastName='Two', doctor=self.doctor_1)
		Patient.objects.create(firstName='C', lastName='Three', doctor=self.doctor_2)
		Patient.objects.create(firstName='D', lastName='Four')

		response = self.client.get(f'/api/doctors/{self.doctor_1.pk}/patients/')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		ids = {item['id'] for item in data}
		self.assertEqual(ids, {str(p1.pk), str(p2.pk)})
		for item in data:
			self.assertEqual(item['doctorId'], str(self.doctor_1.pk))

	def test_patients_collection_can_filter_by_doctor_id_query_param(self):
		p1 = Patient.objects.create(firstName='E', lastName='Five', doctor=self.doctor_1)
		Patient.objects.create(firstName='F', lastName='Six', doctor=self.doctor_2)
		Patient.objects.create(firstName='G', lastName='Seven')

		response = self.client.get(f'/api/patients/?doctorId={self.doctor_1.pk}')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0]['id'], str(p1.pk))
		self.assertEqual(data[0]['doctorId'], str(self.doctor_1.pk))

	def test_patients_collection_filter_by_invalid_doctor_returns_404(self):
		response = self.client.get('/api/patients/?doctorId=invalid-doctor-id')

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.json()['error'], 'Doctor not found')

	def test_patient_studies_endpoint_returns_only_patient_studies(self):
		patient_1 = Patient.objects.create(firstName='P', lastName='One', doctor=self.doctor_1)
		patient_2 = Patient.objects.create(firstName='P', lastName='Two', doctor=self.doctor_2)
		s1 = Study.objects.create(orthancStudyId='ORTH-001', patient=patient_1)
		s2 = Study.objects.create(orthancStudyId='ORTH-002', patient=patient_1)
		Study.objects.create(orthancStudyId='ORTH-003', patient=patient_2)

		response = self.client.get(f'/api/patients/{patient_1.pk}/studies-db/')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		ids = {item['id'] for item in data}
		self.assertEqual(ids, {str(s1.pk), str(s2.pk)})
		for item in data:
			self.assertEqual(item['patientId'], str(patient_1.pk))

	def test_studies_collection_can_filter_by_patient_id_query_param(self):
		patient_1 = Patient.objects.create(firstName='Q', lastName='One', doctor=self.doctor_1)
		patient_2 = Patient.objects.create(firstName='Q', lastName='Two', doctor=self.doctor_2)
		s1 = Study.objects.create(orthancStudyId='ORTH-004', patient=patient_1)
		Study.objects.create(orthancStudyId='ORTH-005', patient=patient_2)

		response = self.client.get(f'/api/studies-db/?patientId={patient_1.pk}')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0]['id'], str(s1.pk))
		self.assertEqual(data[0]['patientId'], str(patient_1.pk))

	def test_studies_collection_filter_by_invalid_patient_returns_404(self):
		response = self.client.get('/api/studies-db/?patientId=invalid-patient-id')

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.json()['error'], 'Patient not found')


class ConsultationsEndpointsTests(TestCase):
	def setUp(self):
		self.doctor = Doctor.objects.create(
			firstName='Rosa',
			lastName='Diaz',
			email='rosa@example.com',
			phone='555-333',
			role=Doctor.ROLE_RADIOLOGIST,
			passwordHash='secret',
		)
		self.patient_1 = Patient.objects.create(
			firstName='Juan',
			lastName='Ruiz',
			doctor=self.doctor,
		)
		self.patient_2 = Patient.objects.create(
			firstName='Ana',
			lastName='Mora',
			doctor=self.doctor,
		)

	def test_create_consultation_returns_201(self):
		scheduled_at = (timezone.now() + timedelta(hours=1)).isoformat()
		payload = {
			'patientId': str(self.patient_1.pk),
			'doctorId': str(self.doctor.pk),
			'scheduledAt': scheduled_at,
		}

		response = self.client.post(
			'/api/consultations/',
			data=json.dumps(payload),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		data = response.json()
		self.assertEqual(data['patientId'], str(self.patient_1.pk))
		self.assertEqual(data['doctorId'], str(self.doctor.pk))
		self.assertEqual(data['status'], Consultation.STATUS_CONFIRMED)

	def test_patient_consultations_returns_only_target_patient(self):
		c1 = Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=timezone.now() + timedelta(hours=2),
		)
		c2 = Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=timezone.now() + timedelta(hours=3),
		)
		Consultation.objects.create(
			patient=self.patient_2,
			doctor=self.doctor,
			scheduledAt=timezone.now() + timedelta(hours=4),
		)

		response = self.client.get(f'/api/patients/{self.patient_1.pk}/consultations/')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		ids = {item['id'] for item in data}
		self.assertEqual(ids, {str(c1.pk), str(c2.pk)})

	def test_confirm_and_cancel_consultation_updates_status(self):
		consultation = Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=timezone.now() + timedelta(hours=1),
			status=Consultation.STATUS_CONFIRMED,
		)

		cancel_response = self.client.put(f'/api/consultations/{consultation.pk}/cancel/')
		self.assertEqual(cancel_response.status_code, 200)
		self.assertEqual(cancel_response.json()['status'], Consultation.STATUS_CANCELED)

		confirm_response = self.client.put(f'/api/consultations/{consultation.pk}/confirm/')
		self.assertEqual(confirm_response.status_code, 200)
		self.assertEqual(confirm_response.json()['status'], Consultation.STATUS_CONFIRMED)

	def test_patient_detail_includes_last_consultation_at(self):
		earlier = timezone.now() + timedelta(hours=1)
		latest = timezone.now() + timedelta(hours=5)

		Consultation.objects.create(patient=self.patient_1, doctor=self.doctor, scheduledAt=earlier)
		Consultation.objects.create(patient=self.patient_1, doctor=self.doctor, scheduledAt=latest)

		response = self.client.get(f'/api/patients/{self.patient_1.pk}/')

		self.assertEqual(response.status_code, 200)
		expected_latest = latest.replace(microsecond=(latest.microsecond // 1000) * 1000)
		self.assertEqual(response.json()['lastConsultationAt'], expected_latest.isoformat())

	def test_doctor_agenda_includes_totals_next_and_list(self):
		now = timezone.now()
		past_confirmed = now - timedelta(hours=1)
		next_confirmed = now + timedelta(minutes=30)
		later_confirmed = now + timedelta(hours=2)
		today_canceled = now + timedelta(hours=3)
		tomorrow_confirmed = now + timedelta(days=1)

		Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=past_confirmed,
			status=Consultation.STATUS_CONFIRMED,
		)
		Consultation.objects.create(
			patient=self.patient_2,
			doctor=self.doctor,
			scheduledAt=next_confirmed,
			status=Consultation.STATUS_CONFIRMED,
		)
		Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=later_confirmed,
			status=Consultation.STATUS_CONFIRMED,
		)
		Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=today_canceled,
			status=Consultation.STATUS_CANCELED,
		)
		Consultation.objects.create(
			patient=self.patient_1,
			doctor=self.doctor,
			scheduledAt=tomorrow_confirmed,
			status=Consultation.STATUS_CONFIRMED,
		)

		response = self.client.get(f'/api/doctors/{self.doctor.pk}/agenda/')

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data['totalConsultationsToday'], 4)
		self.assertEqual(data['consultationsToday'], 3)
		self.assertEqual(data['nextConsultationTime'], timezone.localtime(next_confirmed).strftime('%H:%M'))
		self.assertEqual(len(data['consultations']), 3)
		self.assertEqual(data['consultations'][0]['patientName'], f'{self.patient_1.firstName} {self.patient_1.lastName}')
