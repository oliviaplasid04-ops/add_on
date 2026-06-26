import pandas as pd
import os
from datetime import datetime

LOG_FILE = "data/complaint_log.csv"

def clean_text(text: str) -> str:
    return " ".join(str(text).replace("\n", " ").replace("\r", " ").split())

def save_to_log(name, complaint, category, sentiment, priority, response):
    record = {
        "timestamp": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        "name": clean_text(name),
        "complaint": clean_text(complaint),
        "category": clean_text(category),
        "sentiment": clean_text(sentiment),
        "priority": clean_text(priority),
        "response": clean_text(response),
        "alert": "YES" if priority == "High" else "NO"
    }
    df_new = pd.DataFrame([record])
    if os.path.exists(LOG_FILE):
        df_existing = pd.read_csv(LOG_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        os.makedirs("data", exist_ok=True)
        df_combined = df_new
    df_combined.to_csv(LOG_FILE, index=False)
    return df_combined

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["timestamp","name","complaint","category",
                                  "sentiment","priority","response","alert"])

def delete_complaint(index: int):
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        df = df.drop(index=index).reset_index(drop=True)
        df.to_csv(LOG_FILE, index=False)
