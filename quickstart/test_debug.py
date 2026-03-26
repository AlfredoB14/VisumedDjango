import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickstart.settings')
django.setup()

import requests
from django.conf import settings

orthanc_study_id = "ee44d1f7-6fd75bcb-ae051007-677351ca-759382ea"
base = settings.ORTHANC_URL
auth = (settings.ORTHANC_USER, settings.ORTHANC_PASS)

print(f"Base URL: {base}")
print(f"Auth: {auth}")

try:
    study_url = f"{base}/studies/{orthanc_study_id}"
    print(f"Study URL: {study_url}")
    study_response = requests.get(study_url, auth=auth, timeout=15)
    print(f"Study response status: {study_response.status_code}")
    print(f"Study response text: {study_response.text[:500]}")
    study_data = study_response.json()
    series_ids = study_data.get('Series', [])
    print(f"Series count: {len(series_ids)}")
    if series_ids:
        print(f"First series ID: {series_ids[0]}")
except Exception as e:
    import traceback
    print(f"Error: {type(e).__name__}: {e}")
    traceback.print_exc()
