from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv
# allow CORS
from fastapi.middleware.cors import CORSMiddleware
# allow CORS all origins

load_dotenv()


# FastAPI setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# The data file to store alerts
DATA_FILE = 'alerts.json'

if os.getenv('LINE_NOTIFY_TOKEN') is None:
    raise Exception('LINE_NOTIFY_TOKEN is not set in .env file')

# LINE Notify setup
LINE_NOTIFY_TOKEN = os.getenv('LINE_NOTIFY_TOKEN')
LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'


def send_line_notify(notification_message):
    """
    Send LINE Notify Notification
    """
    headers = {'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'}
    data = {'message': notification_message}
    requests.post(LINE_NOTIFY_API, headers=headers, data=data)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = []
    return data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.post("/webhook")
async def tradingview_alert(request_body: Dict):
    data = load_data()
    data.append(request_body)
    save_data(data)

    # Send LINE Notify notification
    send_line_notify(f"Received a new TradingView alert: {request_body}")

    return {"message": "Alert received and notification sent."}

@app.get("/alerts")
def read_alerts():
    alerts = load_data()
    return alerts

@app.delete("/alerts")
def delete_alerts():
    save_data([])
    return {"message": "All alerts deleted."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)