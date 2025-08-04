import os
import gdown

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../model2_reccomender')
MODEL_PATH = os.path.join(MODEL_DIR, "model.safetensors")
DRIVE_ID = "1Qs61LZA2z7J2gRnY0iLtAy4ZlL_h3_Eg"

def ensure_model_downloaded():
    if not os.path.exists(MODEL_PATH):
        print("model.safetensors not found. Downloading from Google Drive...")
        gdown.download(f"https://drive.google.com/uc?id={DRIVE_ID}", MODEL_PATH, quiet=False)
