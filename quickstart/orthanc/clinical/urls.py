from django.urls import path

from . import views

urlpatterns = [
    path('doctors/', views.doctors_collection, name='doctors_collection'),
    path('doctors/login/', views.doctor_login, name='doctor_login'),
    path('doctors/<str:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('patients/', views.patients_collection, name='patients_collection'),
    path('patients/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('studies-db/', views.studies_collection, name='studies_collection'),
    path('studies-db/<str:study_id>/', views.study_detail, name='study_detail'),
    path('reports/', views.reports_collection, name='reports_collection'),
    path('reports/<str:report_id>/', views.report_detail, name='report_detail'),
]
