import pandas as pd
import joblib
import psycopg2
from psycopg2.extras import execute_values
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import os
import django
import sys
import logging
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up Django
sys.path.append(r'C:\Users\LENOVO\job_recommendation_system\job_rec')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
django.setup()

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

# Text preprocessing function
def preprocess_text(text):
    logger.info("Preprocessing text")
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

# Database connection
logger.info("Connecting to database")
db_settings = settings.DATABASES['default']
try:
    conn = psycopg2.connect(
        dbname=db_settings['NAME'],
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        host=db_settings['HOST'],
        port=db_settings['PORT']
    )
    cursor = conn.cursor()
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise

# Fetch data from the jobs table
logger.info("Fetching data from jobs table")
cursor.execute("SELECT id, title, company, location, job_type, date_posted, url, created_at, source, description FROM jobs")
rows = cursor.fetchall()
if not rows:
    logger.warning("No data found in jobs table")
    cursor.close()
    conn.close()
    raise ValueError("No data found in jobs table")

# Prepare data for prediction
job_data = []
for row in rows:
    job_id, title, company, location, job_type, date_posted, url, created_at, source, description = row
    if pd.isna(description) or description == "":
        description = title
    text = f"{title} {description}"
    job_data.append((title, company, location, job_type, date_posted, url, source, description, text))

# Predict categories (industries)
titles = [item[0] for item in job_data]
descriptions = [item[7] for item in job_data]
texts = [item[8] for item in job_data]
companies = [item[1] for item in job_data]
locations = [item[2] for item in job_data]
job_types = [item[3] for item in job_data]
date_posteds = [item[4] for item in job_data]
urls = [item[5] for item in job_data]
sources = [item[6] for item in job_data]

# Load the LabelEncoder
label_encoder_path = r'C:\Users\LENOVO\job_recommendation_system\job_rec\job_recommendation\model\label_encoder.pkl'
logger.info(f"Loading LabelEncoder from {label_encoder_path}")
if not os.path.exists(label_encoder_path):
    logger.error(f"LabelEncoder file not found at {label_encoder_path}")
    raise FileNotFoundError(f"LabelEncoder file not found at {label_encoder_path}")
label_encoder = joblib.load(label_encoder_path)

# Load BERT model and tokenizer
model_path = r'C:\Users\LENOVO\job_recommendation_system\job_rec\job_recommendation\model'
logger.info(f"Loading BERT model from {model_path}")
try:
    model = BertForSequenceClassification.from_pretrained(model_path)
    tokenizer = BertTokenizer.from_pretrained(model_path)
    
    # Enable gradient checkpointing to save memory
    model.gradient_checkpointing_enable()
    
    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    logger.info(f"Model moved to {device}")
    
    # Preprocess texts
    logger.info("Preprocessing texts for BERT")
    texts_preprocessed = [preprocess_text(text) for text in texts]
    
    # Process texts in batches to avoid memory issues
    batch_size = 4  # Adjust based on your system's memory
    predictions = []
    logger.info("Running BERT predictions in batches")
    
    for i in range(0, len(texts_preprocessed), batch_size):
        batch_texts = texts_preprocessed[i:i + batch_size]
        try:
            # Tokenize batch
            inputs = tokenizer(
                batch_texts,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=128  # Reduced sequence length
            )
            inputs = {key: val.to(device) for key, val in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = model(**inputs)
                batch_predictions = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                predictions.extend(batch_predictions)
            
            # Clear memory
            del inputs, outputs, batch_predictions
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except RuntimeError as e:
            logger.error(f"Memory error in batch {i//batch_size + 1}: {e}")
            raise
            
    # Decode predictions
    industries = label_encoder.inverse_transform(predictions)
    
except Exception as e:
    logger.error(f"Error loading or using BERT model: {e}")
    raise

# Insert cleaned data into jobs_cleaned table
logger.info("Inserting cleaned data into jobs_cleaned table")
insert_query = """
    INSERT INTO jobs_cleaned (title, company, location, job_type, date_posted, url, source, description, category)
    VALUES %s
    ON CONFLICT (title, company, location, job_type, date_posted, url, source, description) DO UPDATE
    SET category = EXCLUDED.category
"""
insert_data = [(
    title, company, location, job_type, date_posted, url, source, description, category
) for title, company, location, job_type, date_posted, url, source, description, category in zip(
    titles, companies, locations, job_types, date_posteds, urls, sources, descriptions, industries
)]
execute_values(cursor, insert_query, insert_data, page_size=1000)

# Commit changes and close connection
logger.info("Committing changes and closing database connection")
conn.commit()
cursor.close()
conn.close()

print("Categorization and insertion completed.")