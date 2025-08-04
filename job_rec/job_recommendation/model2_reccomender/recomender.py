# -----------------------------------------------------
# STEP 0: Install packages if needed
# -----------------------------------------------------
# pip install transformers torch pandas scikit-learn joblib

# -----------------------------------------------------
# STEP 1: Imports
# -----------------------------------------------------
import pandas as pd
import torch
from transformers import BertTokenizer, BertModel
import joblib

# -----------------------------------------------------
# STEP 2: File Paths
# -----------------------------------------------------
USER_CSV = "user_data.csv"
JOBS_CSV = "jobs_data.csv"  # <-- Make sure this exists
MODEL_PATH = "model2_reccomender/ml_model.pkl"
BERT_PATH = "model2_reccomender"

# -----------------------------------------------------
# STEP 3: Load User and Job Data
# -----------------------------------------------------
user_df = pd.read_csv(USER_CSV)
job_df = pd.read_csv(JOBS_CSV)  # Should have at least a 'job_description' column

# Use first user for prediction
user = user_df.iloc[0]
user_text = f"{user['academic_qualification']}, {user['skills']}, {user['about']}, {user['experience']} years experience"

# -----------------------------------------------------
# STEP 4: Load BERT Model & Tokenizer
# -----------------------------------------------------
tokenizer = BertTokenizer.from_pretrained(BERT_PATH)
bert_model = BertModel.from_pretrained(BERT_PATH)
bert_model.eval()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
bert_model.to(device)

# -----------------------------------------------------
# STEP 5: Load Trained Classifier
# -----------------------------------------------------
ml_model = joblib.load(MODEL_PATH)

# -----------------------------------------------------
# STEP 6: Define Embedding Function
# -----------------------------------------------------
def get_bert_embedding(user_text, job_text):
    inputs = tokenizer(
        user_text,
        job_text,
        padding='max_length',
        truncation=True,
        max_length=128,
        return_tensors='pt'
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = bert_model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
    return cls_embedding

# -----------------------------------------------------
# STEP 7: Generate Predictions
# -----------------------------------------------------
predictions = []

for _, job in job_df.iterrows():
    job_text = job['job_description']
    emb = get_bert_embedding(user_text, job_text)
    pred = ml_model.predict([emb])[0]  # 0 or 1
    predictions.append({
        "job_description": job_text,
        "match": int(pred)
    })

# -----------------------------------------------------
# STEP 8: Show Results
# -----------------------------------------------------
result_df = pd.DataFrame(predictions)
matching_jobs = result_df[result_df['match'] == 1]

print("\n✅ Matching Jobs Found:")
print(matching_jobs[['job_description']])
