import joblib
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from django.db import models
from .model_utils import ensure_model_downloaded, MODEL_DIR

ensure_model_downloaded()
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, use_safetensors=True)
label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))

def predict_category(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_class = torch.argmax(outputs.logits, dim=1).item()
        return label_encoder.inverse_transform([predicted_class])[0]

# Database models
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)
    date_posted = models.DateField()
    url = models.URLField()
    created_at = models.DateTimeField()
    source = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        db_table = 'jobs'
        managed = False

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
        managed = False

# Categorization function
def categorize_jobs():
    jobs = Job.objects.all()  # Fetch all jobs; adjust filter if needed
    for job in jobs:
        category = predict_category(job.description)  # Categorize based on description
        JobCleaned.objects.create(
            title=job.title,
            company=job.company,
            location=job.location,
            job_type=job.job_type,
            date_posted=job.date_posted,
            url=job.url,
            source=job.source,
            description=job.description,
            category=category
        )

# Example view to trigger categorization
from django.http import HttpResponse

def process_jobs(request):
    categorize_jobs()
    return HttpResponse("Jobs categorized and saved successfully.")