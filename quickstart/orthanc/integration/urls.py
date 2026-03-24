from django.urls import path

from . import views

urlpatterns = [
    path('studies/', views.get_all_studies, name='get_all_studies'),
    path('studies/<str:study_id>/images/', views.get_study_images, name='get_study_images'),
    path('studies/<str:study_id>/metadata/', views.get_study_metadata, name='get_study_metadata'),
    path('instances/<str:instance_id>/rendered/', views.get_rendered_instance, name='get_rendered_instance'),
]
