# dailyquote
Random daily quotes

Step-by-step (high level, no assumptions)
1. Create a Slack app (5–10 minutes)

Go to api.slack.com → Your Apps → Create New App

Choose From scratch

Give it a name (e.g. “Daily Quote Bot”)

Bot permissions

Add scope: chat:write

Install the app

Install to your workspace

Copy the Bot User OAuth Token (starts with xoxb-)

Invite the bot to the channel

/invite @Daily Quote Bot

2. Create a GitHub repository (very basic usage)

Go to GitHub → New repository

Name it something like slack-daily-quotes

Public or private — doesn’t matter

Create with a README

That’s it. You won’t need branches, PRs, or anything fancy.

3. Add your quotes file

Create a file called:

quotes.txt


Example content:

Progress beats perfection.
Small improvements compound over time.
Clarity comes from doing the work.
Consistency matters more than intensity.


One quote per line.

4. Add the posting script (Python)

Create a file:

post_quote.py


Contents:

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


You do not need to run this locally.

5. Store secrets safely (no hard-coding)

In your GitHub repo:

Settings → Secrets and variables → Actions

Add secrets:

SLACK_BOT_TOKEN → your xoxb-... token

SLACK_CHANNEL → e.g. #your-channel-name

6. Add the GitHub Actions schedule

Create:

.github/workflows/daily.yml


Contents:

name: Daily Slack Quote

on:
  schedule:
    - cron: "0 22 * * 1-5"   # 08:30 ACDT (adjust if needed)
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install slack_sdk
      - run: python post_quote.py
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}


Notes:

workflow_dispatch lets you manually test it from GitHub

GitHub Actions runs on UTC, so timing may need a one-off adjustment
