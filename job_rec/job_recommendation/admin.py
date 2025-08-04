# job_app/admin.py

from django.contrib import admin
from .models import Job, User

admin.site.register(Job)
admin.site.register(User)
# admin.site.register(JobCategory)
