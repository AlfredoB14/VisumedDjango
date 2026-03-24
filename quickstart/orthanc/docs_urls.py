from django.urls import path

from . import docs_views

urlpatterns = [
    path('studies/', docs_views.docs_get_all_studies),
    path('studies/<str:study_id>/images/', docs_views.docs_get_study_images),
    path('studies/<str:study_id>/metadata/', docs_views.docs_get_study_metadata),
    path('instances/<str:instance_id>/rendered/', docs_views.docs_get_rendered_instance),
    path('doctors/', docs_views.docs_doctors_collection),
    path('doctors/login/', docs_views.docs_doctor_login),
    path('doctors/<str:doctor_id>/', docs_views.docs_doctor_detail),
    path('patients/', docs_views.docs_patients_collection),
    path('patients/<str:patient_id>/', docs_views.docs_patient_detail),
    path('studies-db/', docs_views.docs_studies_collection),
    path('studies-db/<str:study_id>/', docs_views.docs_study_detail),
    path('studies/upload/', docs_views.docs_study_upload),
    path('reports/', docs_views.docs_reports_collection),
    path('reports/<str:report_id>/', docs_views.docs_report_detail),
]
