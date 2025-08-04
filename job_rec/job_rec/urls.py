from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("job_recommendation.urls")),
    path("admin/", admin.site.urls),
]