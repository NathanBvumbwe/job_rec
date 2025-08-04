import pandas as pd
import joblib
import psycopg2
from psycopg2.extras import execute_values
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from .model_utils import ensure_model_downloaded, MODEL_DIR

def test_model():
    ensure_model_downloaded()
    model_path = os.path.join(MODEL_DIR, "model.safetensors")
    # ...existing code...

def run_categorization_pipeline():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
    try:
        django.setup()
    except Exception as e:
        logger.error(f"Failed to set up Django: {e}")
        raise

    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

    def preprocess_text(text):
        # ... (function logic) ...
        return ' '.join(tokens)

    # Ensure model.safetensors exists in model2_reccomender
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../model2_reccomender/model.safetensors")
    DRIVE_ID = "1Qs61LZA2z7J2gRnY0iLtAy4ZlL_h3_Eg"
    if not os.path.exists(model_path):
        print("model.safetensors not found. Downloading from Google Drive...")
        gdown.download(f"https://drive.google.com/uc?id={DRIVE_ID}", model_path, quiet=False)
    if not os.path.exists(model_path):
        url = "https://drive.google.com/uc?id=1Qs61LZA2z7J2gRnY0iLtAy4ZlL_h3_Eg"
        gdown.download(url, model_path, quiet=False)

    # ... (rest of the functions and main logic as provided before) ...
    # It will use os.path.join(settings.BASE_DIR, ...) for paths