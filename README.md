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


--------


UPDATE:Randomised posting on Monday and Friday only during working hours

--------
Yes — it’s possible on GitHub Actions, with one caveat:

GitHub Actions schedules (cron) are fixed times in UTC (no native “pick a random time each day”).

But you can simulate randomness by running the workflow periodically during the business-hours window, and having your script post only once at a “randomly chosen” slot.

That gives you:

only Mondays + Fridays (Adelaide local day)

a posting time that varies each day, somewhere between 9:00 and 17:00 Adelaide time

no external services

Below is the cleanest approach I’d recommend: 30-minute resolution (you can change it to 15 minutes if you like).

1) Update the workflow schedule (GitHub Actions)

Edit .github/workflows/daily.yml and replace your on: schedule: with this:

on:
  schedule:
    # Run every 30 minutes during the UTC window that covers 9–5 in Adelaide
    # across both ACST and ACDT (we'll gate in code so it only posts Mon/Fri).
    - cron: "0,30 22-23,0-8 * * 0,1"   # Sun+Mon UTC (covers Monday Adelaide)
    - cron: "0,30 22-23,0-8 * * 4,5"   # Thu+Fri UTC (covers Friday Adelaide)
  workflow_dispatch:


Why this works:

Adelaide 9–5 falls roughly in UTC evening → UTC morning, depending on DST.

This schedule creates “checkpoints” across that whole range.

Your script decides whether “this run is the chosen random time slot”.

2) Add one new GitHub secret (seed for randomness)

In your repo Secrets (Settings → Secrets and variables → Actions), add:

SCHEDULE_SEED = any random string (e.g. h7v3-...)

This makes the “random time” stable and not guessable.
(You could reuse another secret, but I prefer keeping concerns separate.)

3) Update post_quote.py to post only once per day (Mon/Fri) at a “random” slot

Replace your post_quote.py with this:

import os
import random
import hashlib
from datetime import datetime, time
from zoneinfo import ZoneInfo

from slack_sdk import WebClient


ADELAIDE = ZoneInfo("Australia/Adelaide")

WINDOW_START = time(9, 0)    # 09:00
WINDOW_END   = time(17, 0)   # 17:00 (end-exclusive)
SLOT_MINUTES = 30            # change to 15 if you want finer randomness


def _minutes_since(t: time) -> int:
    return t.hour * 60 + t.minute


def should_post_now(now: datetime, seed: str) -> bool:
    # Only Mondays and Fridays, Adelaide local time
    # Python weekday: Mon=0 ... Sun=6
    if now.weekday() not in (0, 4):
        return False

    local_t = now.timetz()
    if not (WINDOW_START <= local_t.replace(tzinfo=None) < WINDOW_END):
        return False

    start_m = _minutes_since(WINDOW_START)
    end_m = _minutes_since(WINDOW_END)
    now_m = now.hour * 60 + now.minute

    slots = list(range(start_m, end_m, SLOT_MINUTES))  # e.g. 09:00, 09:30, ... 16:30
    if not slots:
        return False

    # Deterministic "random" slot per local date (so exactly one slot is chosen)
    date_str = now.date().isoformat()  # Adelaide local date
    h = hashlib.sha256((seed + "|" + date_str).encode("utf-8")).digest()
    chosen_index = int.from_bytes(h[:4], "big") % len(slots)
    chosen_minute_of_day = slots[chosen_index]

    # Are we currently at that slot boundary?
    return now_m == chosen_minute_of_day


def load_random_quote() -> str:
    with open("quotes.txt", "r", encoding="utf-8") as f:
        quotes = [q.strip() for q in f if q.strip()]
    return random.choice(quotes)


def main():
    seed = os.environ.get("SCHEDULE_SEED", "default-seed")
    now = datetime.now(ADELAIDE).replace(second=0, microsecond=0)

    if not should_post_now(now, seed):
        print(f"Not posting. Adelaide now: {now.isoformat()}")
        return

    quote = load_random_quote()

    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(
        channel=os.environ["SLACK_CHANNEL"],
        text=f"Morning thought:\n> {quote}"
    )
    print(f"Posted. Adelaide now: {now.isoformat()}")


if __name__ == "__main__":
    main()


And update your workflow to pass the new secret into the script:

      - run: python post_quote.py
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}
          SCHEDULE_SEED: ${{ secrets.SCHEDULE_SEED }}

What you’ll get

The workflow “wakes up” every 30 minutes during the possible window.

The script computes a single chosen slot for that Adelaide date.

It posts exactly once on Monday and exactly once on Friday.

The exact time varies week to week, but stays within 9–5 Adelaide.

Want the randomness to feel smoother?

If you want more variation, change:

SLOT_MINUTES = 30 → 15

and in the workflow cron minutes: 0,30 → 0,15,30,45

That yields 15-minute granularity.

If you paste your current .yml and confirm whether you prefer 30 or 15 minute granularity, I’ll give you the exact final YAML block to drop in with no guesswork.
