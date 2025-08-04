# --------------------------------------------
# STEP 0: Install dependencies if needed
# --------------------------------------------
# pip install transformers safetensors torch scikit-learn pandas seaborn matplotlib

# --------------------------------------------
# STEP 1: Imports
# --------------------------------------------
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, AutoConfig
from safetensors.torch import load_file
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------------------
# STEP 2: Paths
# --------------------------------------------
# MODEL_DIR = "C:/Users/LENOVO/job_recommendation_system/job_rec/job_recommendation/model2_reccomender"
MODEL_DIR = "C:\\Users\\LENOVO\\job_recommendation_system\\job_rec\\job_recommendation\\model2_reccomender"
TEST_DATA_PATH = "user_data.csv"  # Make sure this CSV exists

# --------------------------------------------
# STEP 3: Load Config, Tokenizer, Model
# --------------------------------------------
config = AutoConfig.from_pretrained(MODEL_DIR)
tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
model = BertForSequenceClassification(config)
model.load_state_dict(load_file(f"{MODEL_DIR}/model.safetensors"))
model.eval()

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# --------------------------------------------
# STEP 4: Load and Prepare Test Data
# --------------------------------------------
df_test = pd.read_csv(TEST_DATA_PATH)  # Columns: user_profile, job_description, label

class JobMatchingDataset(Dataset):
    def __init__(self, df, tokenizer, max_length=256):
        self.df = df
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        user_text = self.df.iloc[idx]['user_profile']
        job_text = self.df.iloc[idx]['job_description']
        label = self.df.iloc[idx]['label']

        encoded = self.tokenizer(
            user_text,
            job_text,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoded['input_ids'].squeeze(),
            'attention_mask': encoded['attention_mask'].squeeze(),
            'labels': torch.tensor(label)
        }

test_dataset = JobMatchingDataset(df_test, tokenizer)
test_loader = DataLoader(test_dataset, batch_size=16)

# --------------------------------------------
# STEP 5: Evaluate the Model
# --------------------------------------------
all_preds = []
all_labels = []

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        preds = torch.argmax(logits, dim=1)

        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

# --------------------------------------------
# STEP 6: Metrics and Confusion Matrix
# --------------------------------------------
print("Classification Report:")
print(classification_report(all_labels, all_preds))

print("\nConfusion Matrix:")
cm = confusion_matrix(all_labels, all_preds)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot(cmap="Blues")
plt.title("Confusion Matrix")
plt.show()
