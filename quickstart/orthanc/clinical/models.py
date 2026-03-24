from django.db import models


class Doctor(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_RADIOLOGIST = 'radiologist'
    ROLE_REFERRING = 'referring'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_RADIOLOGIST, 'Radiologist'),
        (ROLE_REFERRING, 'Referring'),
    ]

    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    passwordHash = models.CharField(max_length=255)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.role})"


class Patient(models.Model):
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
    ]

    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    birthDate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    address = models.CharField(max_length=255, blank=True)
    postalCode = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=100, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName}"


class Study(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    orthancStudyId = models.CharField(max_length=255, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='studies')
    referringDoctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_studies'
    )
    interpretingDoctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interpreted_studies'
    )
    modality = models.CharField(max_length=20, blank=True)
    bodyPart = models.CharField(max_length=100, blank=True)
    studyDate = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study {self.orthancStudyId} - {self.patient}"


class Report(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SIGNED = 'signed'
    STATUS_AMENDED = 'amended'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SIGNED, 'Signed'),
        (STATUS_AMENDED, 'Amended'),
    ]

    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='reports')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    studyName = models.CharField(max_length=255, blank=True)
    technique = models.CharField(max_length=255, blank=True)
    studyDate = models.DateField(null=True, blank=True)
    indication = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    priorStudies = models.TextField(blank=True)
    conclusions = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.pk} - {self.status}"
