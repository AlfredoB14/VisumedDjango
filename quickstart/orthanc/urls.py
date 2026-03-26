from django.urls import include, path
from .views import StudyAxialView, StudySagittalView, StudyCoronalView, StudyDebugView

urlpatterns = [
    path('', include('orthanc.integration.urls')),
    path('', include('orthanc.clinical.urls')),
    path('studies/<str:orthanc_study_id>/images/axial/', StudyAxialView.as_view()),
    path('studies/<str:orthanc_study_id>/images/sagittal/', StudySagittalView.as_view()),
    path('studies/<str:orthanc_study_id>/images/coronal/', StudyCoronalView.as_view()),
    path('studies/<str:orthanc_study_id>/debug/', StudyDebugView.as_view()),
]
