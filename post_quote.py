import random
import os
from slack_sdk import WebClient

with open("quotes.txt", "r", encoding="utf-8") as f:
    quotes = [q.strip() for q in f if q.strip()]

quote = random.choice(quotes)

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

client.chat_postMessage(
    channel=os.environ["SLACK_CHANNEL"],
    text=f"Morning thought:\n> {quote}"
)
