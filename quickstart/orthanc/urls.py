from django.urls import include, path

urlpatterns = [
    path('', include('orthanc.integration.urls')),
    path('', include('orthanc.clinical.urls')),
]
