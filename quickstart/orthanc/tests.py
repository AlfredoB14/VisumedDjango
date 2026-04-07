import json

from django.test import TestCase

from orthanc.clinical.models import Doctor, Patient, Study


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
