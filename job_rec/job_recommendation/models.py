from django.db import models
from django.contrib.postgres.fields import ArrayField

# class JobCategory(models.Model):
#     name = models.CharField(max_length=100)
#
#     def __str__(self):
#         return self.name

class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    academic_qualification = models.CharField(max_length=100)
    experience = models.CharField(max_length=100)
    skills = ArrayField(models.CharField(max_length=100), default=list)
    about = models.TextField()
    password = models.CharField(max_length=128)  # For storing hashed passwords

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'password']

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = 'user'
        managed = True

    def __str__(self):
        return self.name

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)
    date_posted = models.DateField()
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)  # <-- THIS LINE IS NOW FIXED
    source = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        db_table = 'jobs'
        managed = True

# --- New models for job seeker functionalities ---

class SavedJob(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_job'
        unique_together = ('user', 'job')
        managed = True

class Resume(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')
    parsed_skills = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resume'
        managed = True

class JobAlertPreference(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    keywords = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    locations = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    job_types = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    remote_on_site = ArrayField(models.CharField(max_length=10), default=list, blank=True)

    class Meta:
        db_table = 'job_alert_preference'
        managed = True

class Notification(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'notification'
        managed = True

class JobCleaned(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)
    date_posted = models.DateField()
    url = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=100)

    class Meta:
        db_table = 'jobs_cleaned'
        managed = True

class Recruiter(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    position = models.CharField(max_length=100)  # e.g., HR Manager, Recruiter, etc.
    contact_phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    hiring_needs = models.TextField(help_text="Describe your current hiring needs")
    about_company = models.TextField()
    website = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    password = models.CharField(max_length=128)  # For storing hashed passwords
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'password']

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = 'recruiter'
        managed = True

    def __str__(self):
        return f"{self.name} - {self.company_name}"

class MatchedJob(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=255)
    user_email = models.EmailField()
    job_id = models.IntegerField()
    job_title = models.CharField(max_length=255)
    job_category = models.CharField(max_length=100)
    similarity_score = models.FloatField()

    class Meta:
        db_table = 'matched_jobs'
        unique_together = ('user_id', 'job_id')