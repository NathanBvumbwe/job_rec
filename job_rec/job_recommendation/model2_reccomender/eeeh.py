import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
import os
import itertools

# --------------------------------------------
# STEP 1: Configuration
# --------------------------------------------
MODEL_DIR = r"C:\Users\LENOVO\job_recommendation_system\job_rec\job_recommendation\model2_reccomender"
USER_DATA_PATH = r"job_rec\job_recommendation\model2_reccomender\user_data.csv"
JOB_LISTINGS_PATH = r"job_rec\job_recommendation\model2_reccomender\data.csv"
BATCH_SIZE = 16
MAX_LENGTH = 256
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Verify file paths
print(f"Model directory exists: {os.path.exists(MODEL_DIR)}")
print(f"User data file exists: {os.path.exists(USER_DATA_PATH)}")
print(f"Job listings file exists: {os.path.exists(JOB_LISTINGS_PATH)}")

# --------------------------------------------
# STEP 2: Load Model and Tokenizer
# --------------------------------------------
def load_model_and_tokenizer(model_dir):
    try:
        tokenizer = BertTokenizer.from_pretrained(model_dir)
        model = BertForSequenceClassification.from_pretrained(model_dir)
        model.to(DEVICE)
        model.eval()
        print(f"Model config: {model.config}")
        print(f"Number of labels: {model.config.num_labels}")
        return tokenizer, model
    except Exception as e:
        raise ValueError(f"Failed to load model or tokenizer from {model_dir}: {str(e)}")

if not os.path.exists(MODEL_DIR):
    raise FileNotFoundError(f"Model directory {MODEL_DIR} does not exist")

tokenizer, model = load_model_and_tokenizer(MODEL_DIR)

# --------------------------------------------
# STEP 3: Load and Prepare Data
# --------------------------------------------
def load_data(user_file_path, job_file_path):
    if not os.path.exists(user_file_path):
        raise FileNotFoundError(f"User data file {user_file_path} does not exist")
    if not os.path.exists(job_file_path):
        raise FileNotFoundError(f"Job listings file {job_file_path} does not exist")
    
    # Print raw CSV content for debugging
    with open(user_file_path, 'r', encoding='utf-8') as f:
        print("Raw content of user_data.csv:")
        print(f.read())
        f.seek(0)
    
    # Load user profiles
    df_users = pd.read_csv(user_file_path, encoding='utf-8-sig')
    df_users.columns = df_users.columns.str.strip()
    print("Parsed columns in user_data.csv:", df_users.columns.tolist())
    
    required_user_columns = ['email', 'name', 'academic_qualification', 'experience', 'skills', 'about']
    if not all(col in df_users.columns for col in required_user_columns):
        raise ValueError(f"User CSV must contain columns: {required_user_columns}")
    
    # Clean skills column
    df_users['skills'] = df_users['skills'].str.rstrip(',')
    
    # Combine relevant fields into a single user_profile
    df_users['user_profile'] = (
        df_users['academic_qualification'].fillna('No qualification') + " | " +
        df_users['experience'].astype(str).fillna('0') + " years experience | " +
        df_users['skills'].fillna('No skills provided') + " | " +
        df_users['about'].fillna('No description')
    ).astype(str)
    
    # Load job listings
    df_jobs = pd.read_csv(job_file_path, encoding='utf-8')
    df_jobs.columns = df_jobs.columns.str.strip()
    print("Parsed columns in data.csv:", df_jobs.columns.tolist())
    
    required_job_columns = ['id', 'title', 'category']
    if not all(col in df_jobs.columns for col in required_job_columns):
        raise ValueError(f"Job listings CSV must contain columns: {required_job_columns}")
    
    # Combine title and category into a single job_text
    df_jobs['job_text'] = (
        df_jobs['title'].fillna('No title') + " | " +
        df_jobs['category'].fillna('No category')
    ).astype(str)
    
    # Debug: Print sample data
    print("Sample user profiles:")
    print(df_users[['email', 'user_profile']].head())
    print("\nSample job listings:")
    print(df_jobs[['id', 'job_text']].head())
    
    pairs = list(itertools.product(df_users.index, df_jobs.index))
    df_pairs = pd.DataFrame(pairs, columns=['user_idx', 'job_idx'])
    df_pairs['user_profile'] = df_users.loc[df_pairs['user_idx'], 'user_profile'].values
    df_pairs['job_text'] = df_jobs.loc[df_pairs['job_idx'], 'job_text'].values
    
    return df_users, df_jobs, df_pairs

df_users, df_jobs, df_pairs = load_data(USER_DATA_PATH, JOB_LISTINGS_PATH)

# --------------------------------------------
# STEP 4: Define Dataset
# --------------------------------------------
class JobMatchingDataset(Dataset):
    def __init__(self, df, tokenizer, max_length=MAX_LENGTH):
        self.df = df
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        user_text = self.df.iloc[idx]['user_profile']
        job_text = self.df.iloc[idx]['job_text']

        encoded = self.tokenizer(
            user_text,
            job_text,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )

        if idx < 5:
            print(f"Sample {idx}:")
            print(f"User text: {user_text}")
            print(f"Job text: {job_text}")
            print(f"Tokenized input IDs: {encoded['input_ids'].squeeze()[:10]}")
            print(f"Attention mask: {encoded['attention_mask'].squeeze()[:10]}")

        return {
            'input_ids': encoded['input_ids'].squeeze(),
            'attention_mask': encoded['attention_mask'].squeeze(),
            'user_idx': self.df.iloc[idx]['user_idx'],
            'job_idx': self.df.iloc[idx]['job_idx']
        }

dataset = JobMatchingDataset(df_pairs, tokenizer)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

# --------------------------------------------
# STEP 5: Predict Matches
# --------------------------------------------
def predict_matches(model, data_loader, df_users, df_jobs):
    results = []
    pred_counts = {i: 0 for i in range(15)}  # Support 15 labels
    
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            user_indices = batch['user_idx'].tolist()
            job_indices = batch['job_idx'].tolist()

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(logits, dim=1)

            for pred in preds.tolist():
                pred_counts[pred] += 1
            print(f"Batch prediction counts: {pred_counts}")
            print(f"Sample probabilities for LABEL_1: {probs[:, 1][:5].tolist()}")

            for user_idx, job_idx, pred, prob in zip(user_indices, job_indices, preds.tolist(), probs[:, 1].tolist()):
                results.append({
                    'user_email': df_users.iloc[user_idx]['email'],
                    'user_name': df_users.iloc[user_idx]['name'],
                    'job_id': df_jobs.iloc[job_idx]['id'],
                    'job_title': df_jobs.iloc[job_idx]['title'],
                    'job_category': df_jobs.iloc[job_idx]['category'],
                    'user_profile': df_users.iloc[user_idx]['user_profile'],
                    'job_text': df_jobs.iloc[job_idx]['job_text'],
                    'prediction': pred,
                    'match_probability': prob
                })

    print(f"Final prediction counts: {pred_counts}")
    return pd.DataFrame(results)

df_results = predict_matches(model, loader, df_users, df_jobs)

# --------------------------------------------
# STEP 6: Output Results
# --------------------------------------------
# Filter for predicted matches (assuming LABEL_1 is the "match" label)
df_matches = df_results[df_results['prediction'] == 1][[
    'user_email', 'user_name', 'job_id', 'job_title', 'job_category', 'match_probability'
]].sort_values(by='match_probability', ascending=False)
print("Predicted Matches (LABEL_1):")
print(df_matches)

# Save results to CSV
df_matches.to_csv("predicted_matches.csv", index=False)
print("Results saved to 'predicted_matches.csv'")