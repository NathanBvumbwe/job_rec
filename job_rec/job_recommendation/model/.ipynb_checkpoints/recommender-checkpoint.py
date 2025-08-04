import os
import torch
import joblib
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, use_safetensors=True)
label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))

def recommend_category(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()
    category = label_encoder.inverse_transform([predicted_class])[0]
    return category 