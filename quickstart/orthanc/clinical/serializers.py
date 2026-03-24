class DoctorSerializer:
    @staticmethod
    def serialize(obj):
        return {
            'id': str(obj.pk),
            'firstName': obj.firstName,
            'lastName': obj.lastName,
            'email': obj.email,
            'phone': obj.phone,
            'role': obj.role,
            'passwordHash': obj.passwordHash,
            'createdAt': obj.createdAt.isoformat() if obj.createdAt else None,
        }


class PatientSerializer:
    @staticmethod
    def serialize(obj):
        return {
            'id': str(obj.pk),
            'firstName': obj.firstName,
            'lastName': obj.lastName,
            'email': obj.email,
            'phone': obj.phone,
            'birthDate': obj.birthDate.isoformat() if obj.birthDate else None,
            'gender': obj.gender,
            'address': obj.address,
            'postalCode': obj.postalCode,
            'state': obj.state,
            'createdAt': obj.createdAt.isoformat() if obj.createdAt else None,
        }


class StudySerializer:
    @staticmethod
    def serialize(obj):
        return {
            'id': str(obj.pk),
            'orthancStudyId': obj.orthancStudyId,
            'patientId': str(obj.patient_id) if obj.patient_id else None,
            'referringDoctorId': str(obj.referringDoctor_id) if obj.referringDoctor_id else None,
            'interpretingDoctorId': str(obj.interpretingDoctor_id) if obj.interpretingDoctor_id else None,
            'modality': obj.modality,
            'bodyPart': obj.bodyPart,
            'studyDate': obj.studyDate.isoformat() if obj.studyDate else None,
            'status': obj.status,
            'createdAt': obj.createdAt.isoformat() if obj.createdAt else None,
        }


class ReportSerializer:
    @staticmethod
    def serialize(obj):
        return {
            'id': str(obj.pk),
            'studyId': str(obj.study_id) if obj.study_id else None,
            'doctorId': str(obj.doctor_id) if obj.doctor_id else None,
            'studyName': obj.studyName,
            'technique': obj.technique,
            'studyDate': obj.studyDate.isoformat() if obj.studyDate else None,
            'indication': obj.indication,
            'findings': obj.findings,
            'priorStudies': obj.priorStudies,
            'conclusions': obj.conclusions,
            'suggestions': obj.suggestions,
            'status': obj.status,
            'createdAt': obj.createdAt.isoformat() if obj.createdAt else None,
        }
