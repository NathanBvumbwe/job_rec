import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import platform

# Load the BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# USER_DATA_PATH = r"job_rec\job_recommendation\model2_reccomender\user_data.csv"
# JOB_LISTINGS_PATH = r"job_rec\job_recommendation\model2_reccomender\data.csv"

# File paths (adjust as needed for your environment)
USER_DATA_PATH = r"job_rec\job_recommendation\model2_reccomender\user_data.csv"
JOB_LISTINGS_PATH = r"job_rec\job_recommendation\model2_reccomender\data.csv"

# Function to clean and validate data
def clean_data(df, required_columns):
    # Remove empty rows
    df = df.dropna(how='all')
    
    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Clean string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip().replace('', np.nan)
    
    return df

# Function to combine user profile fields
def combine_user_profile(row):
    profile_parts = []
    for field in ['name', 'academic_qualification', 'experience', 'skills', 'about']:
        value = row[field]
        if pd.notna(value) and isinstance(value, str):
            profile_parts.append(value)
    return ' '.join(profile_parts)

# Function to combine job listing fields
def combine_job_fields(row):
    job_parts = []
    for field in ['title', 'category']:
        value = row[field]
        if pd.notna(value) and isinstance(value, str):
            job_parts.append(value)
    return ' '.join(job_parts)

# Function to compute embeddings
def compute_embeddings(texts):
    return model.encode(texts, convert_to_tensor=False)

# Function to match users to jobs
def match_users_to_jobs(user_data, job_data, top_n=5):
    # Combine user and job fields
    user_profiles = user_data.apply(combine_user_profile, axis=1).tolist()
    job_profiles = job_data.apply(combine_job_fields, axis=1).tolist()
    
    # Compute embeddings
    user_embeddings = compute_embeddings(user_profiles)
    job_embeddings = compute_embeddings(job_profiles)
    
    # Compute cosine similarity
    similarity_matrix = cosine_similarity(user_embeddings, job_embeddings)
    
    # Get top N matches for each user
    matches = []
    for user_idx, user_similarities in enumerate(similarity_matrix):
        top_job_indices = np.argsort(user_similarities)[-top_n:][::-1]
        user_matches = [
            {
                'user_id': user_data.iloc[user_idx]['id'],
                'user_name': user_data.iloc[user_idx]['name'],
                'user_email': user_data.iloc[user_idx]['email'],
                'job_id': job_data.iloc[job_idx]['id'],
                'job_title': job_data.iloc[job_idx]['title'],
                'job_category': job_data.iloc[job_idx]['category'],
                'similarity_score': user_similarities[job_idx]
            }
            for job_idx in top_job_indices
        ]
        matches.extend(user_matches)
    
    return pd.DataFrame(matches)

# Django ORM-based recommendation function

def recommend_jobs_for_user(user_id, top_n=5):
    """
    Fetch user and job data from the database, compute semantic similarity, and return top N recommended jobs for the given user_id.
    Returns a list of (job_instance, similarity_score) tuples.
    """
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
    django.setup()
    from job_recommendation.models import User, JobCleaned
    from django.db.models import Q

    # Fetch user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return []

    # Combine user profile fields
    user_profile = ' '.join([
        user.name or '',
        user.academic_qualification or '',
        user.experience or '',
        ', '.join(user.skills) if hasattr(user, 'skills') and user.skills else '',
        user.about or ''
    ])

    # Fetch all jobs from jobs_cleaned
    jobs = list(JobCleaned.objects.all())
    if not jobs:
        return []

    # Combine job fields
    job_profiles = [
        ' '.join([job.title or '', job.category or '']) for job in jobs
    ]

    # Compute embeddings
    user_embedding = compute_embeddings([user_profile])[0]
    job_embeddings = compute_embeddings(job_profiles)

    # Compute cosine similarity
    similarities = cosine_similarity([user_embedding], job_embeddings)[0]

    # Get top N job indices
    top_indices = similarities.argsort()[-top_n:][::-1]

    # Return list of (job_instance, similarity_score)
    return [(jobs[i], similarities[i]) for i in top_indices]

def save_matches_to_db(user_id, top_n=5):
    """
    For a given user_id, compute top N job matches and save them to the MatchedJob table.
    """
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
    django.setup()
    from job_recommendation.models import MatchedJob, User, JobCleaned

    print(f"[DEBUG] Running save_matches_to_db for user_id={user_id}")
    try:
        user = User.objects.get(id=user_id)
        print(f"[DEBUG] Found user: {user.name} ({user.email})")
    except User.DoesNotExist:
        print(f"[DEBUG] User with id {user_id} does not exist.")
        return 0

    jobs = list(JobCleaned.objects.all())
    print(f"[DEBUG] Found {len(jobs)} jobs in JobCleaned table.")

    matches = recommend_jobs_for_user(user_id, top_n=top_n)
    print(f"[DEBUG] Computed {len(matches)} matches.")
    if not matches:
        print("[DEBUG] No matches to save.")
        return 0

    # Clear old matches for this user
    MatchedJob.objects.filter(user_id=user_id).delete()
    print("[DEBUG] Cleared old matches for user.")

    # Save new matches
    for job, score in matches:
        MatchedJob.objects.create(
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            job_id=job.id,
            job_title=job.title,
            job_category=job.category,
            similarity_score=score
        )
        print(f"[DEBUG] Saved match: job_id={job.id}, score={score}")
    print(f"[DEBUG] Done saving {len(matches)} matches for user_id={user_id}.")
    return len(matches)

# Batch process: For all users, compute and save top N job matches to the database

def batch_save_all_matches(top_n=5):
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
    django.setup()
    from job_recommendation.models import User

    users = User.objects.all()
    print(f"[DEBUG] Found {users.count()} users.")
    for user in users:
        print(f"[DEBUG] Processing user: {user.id} - {user.name}")
        try:
            save_matches_to_db(user.id, top_n=top_n)
        except Exception as e:
            print(f"[ERROR] Failed for user {user.id}: {e}")
    print("[DEBUG] Batch matching complete.")

# Remove or comment out all CSV reading/writing and main async logic

if __name__ == "__main__":
    batch_save_all_matches(top_n=6)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

     