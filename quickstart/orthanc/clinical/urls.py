from django.urls import path

from . import views

urlpatterns = [
    path('doctors/', views.doctors_collection, name='doctors_collection'),
    path('doctors/login/', views.doctor_login, name='doctor_login'),
    path('doctors/<str:doctor_id>/agenda/', views.doctor_agenda, name='doctor_agenda'),
    path('doctors/<str:doctor_id>/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctors/<str:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('patients/', views.patients_collection, name='patients_collection'),
    path('patients/<str:patient_id>/consultations/', views.patient_consultations, name='patient_consultations'),
    path('patients/<str:patient_id>/studies-db/', views.patient_studies, name='patient_studies'),
    path('patients/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('consultations/', views.consultations_collection, name='consultations_collection'),
    path('consultations/<str:consultation_id>/confirm/', views.consultation_confirm, name='consultation_confirm'),
    path('consultations/<str:consultation_id>/cancel/', views.consultation_cancel, name='consultation_cancel'),
    path('studies-db/', views.studies_collection, name='studies_collection'),
    path('studies-db/<str:study_id>/', views.study_detail, name='study_detail'),
    path('reports/', views.reports_collection, name='reports_collection'),
    path('reports/<str:report_id>/', views.report_detail, name='report_detail'),
]
