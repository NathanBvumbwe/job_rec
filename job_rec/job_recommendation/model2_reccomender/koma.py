
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import chrono
import json

# Defining helper functions for data cleaning and preprocessing
def clean_text(text):
    if not isinstance(text, str) or text is None:
        return ''
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def parse_date(date_str):
    if not isinstance(date_str, str) or date_str is None:
        return None
    try:
        return chrono.parseDate(date_str)
    except:
        return None

def clean_boolean(value):
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ['true', 'yes', 'on', '1']:
            return True
        if value in ['false', 'no', 'off', '0']:
            return False
    return value

# Loading and processing user and job data
def load_and_clean_data(user_file, job_file):
    # Loading CSV files
    user_data = pd.read_csv(user_file)
    job_data = pd.read_csv(job_file)

    # Cleaning user data
    for col in ['email', 'name', 'address', 'academic qualification', 'experience', 'skills', 'about']:
        if col in user_data.columns:
            user_data[col] = user_data[col].apply(clean_text)

    # Cleaning job data
    for col in ['title', 'category', 'description', 'company', 'location', 'job_type']:
        if col in job_data.columns:
            job_data[col] = job_data[col].apply(clean_text)

    # Cleaning date_posted
    if 'date_posted' in job_data.columns:
        job_data['date_posted'] = job_data['date_posted'].apply(parse_date)

    return user_data, job_data

# Combining user fields for matching
def combine_user_fields(row):
    fields = [row.get(col, '') for col in ['name', 'academic qualification', 'experience', 'skills', 'about']]
    return ' '.join([str(f) for f in fields if f])

# Combining job fields for matching
def combine_job_fields(row):
    fields = [row.get(col, '') for col in ['title', 'category', 'description']]  # Include description
    return ' '.join([str(f) for f in fields if f])

# Generating TF-IDF vectors for matching
def generate_tfidf_vectors(user_data, job_data):
    user_profiles = user_data.apply(combine_user_fields, axis=1)
    job_profiles = job_data.apply(combine_job_fields, axis=1)

    # Combining user and job profiles for TF-IDF
    all_profiles = pd.concat([user_profiles, job_profiles], ignore_index=True)

    # Creating TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(all_profiles)

    # Splitting back into user and job matrices
    user_tfidf = tfidf_matrix[:len(user_data)]
    job_tfidf = tfidf_matrix[len(user_data):]

    return user_tfidf, job_tfidf, vectorizer

# Converting NumPy types to Python native types for JSON serialization
def convert_to_serializable(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# Recommending jobs for a user
def recommend_jobs(user_data, job_data, top_n=5):
    user_tfidf, job_tfidf, vectorizer = generate_tfidf_vectors(user_data, job_data)
    recommendations = []

    for user_idx in range(len(user_data)):
        user_id = user_data.iloc[user_idx].get('user_id', user_idx)
        user_email = user_data.iloc[user_idx].get('email', 'unknown')
        user_name = user_data.iloc[user_idx].get('name', 'unknown')

        # Calculating cosine similarity
        similarities = cosine_similarity(user_tfidf[user_idx], job_tfidf)[0]
        top_indices = np.argsort(similarities)[-top_n:][::-1]

        user_recommendations = []
        for job_idx in top_indices:
            if similarities[job_idx] > 0:  # Only include matches with positive similarity
                job = job_data.iloc[job_idx]
                user_recommendations.append({
                    'job_id': convert_to_serializable(job.get('id', job_idx)),
                    'title': job.get('title', 'unknown'),
                    'company': job.get('company', 'unknown'),
                    'location': job.get('location', 'unknown'),
                    'similarity_score': round(float(similarities[job_idx]), 4)
                })

        recommendations.append({
            'user_id': convert_to_serializable(user_id),
            'name': user_name,
            'email': user_email,
            'recommended_jobs': user_recommendations
        })

    return recommendations

# Saving recommendations to JSON
def save_recommendations(recommendations, output_file):
    # Convert all recommendations to JSON-serializable format
    serializable_recommendations = []
    for rec in recommendations:
        serializable_rec = {
            'user_id': convert_to_serializable(rec['user_id']),
            'name': rec['name'],
            'email': rec['email'],
            'recommended_jobs': [
                {key: convert_to_serializable(value) for key, value in job.items()}
                for job in rec['recommended_jobs']
            ]
        }
        serializable_recommendations.append(serializable_rec)
    
    with open(output_file, 'w') as f:
        json.dump(serializable_recommendations, f, indent=2)

# Main function to run the recommendation system
def main(user_file, job_file, output_file):
    try:
        user_data, job_data = load_and_clean_data(user_file, job_file)
        recommendations = recommend_jobs(user_data, job_data)
        save_recommendations(recommendations, output_file)
        print(f"Recommendations saved to {output_file}")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Example file paths (adjust as needed)
    USER_FILE = r"job_rec\job_recommendation\model2_reccomender\user_data.csv"
    JOB_FILE = r"job_rec\job_recommendation\model2_reccomender\data.csv"
    OUTPUT_FILE = "recommendations.json"
    main(USER_FILE, JOB_FILE, OUTPUT_FILE)
