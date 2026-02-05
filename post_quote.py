import os
import random
import hashlib
from datetime import datetime, time
from zoneinfo import ZoneInfo

from slack_sdk import WebClient

ADELAIDE = ZoneInfo("Australia/Adelaide")

WINDOW_START = time(9, 0)   # 09:00
WINDOW_END = time(17, 0)    # 17:00 (end-exclusive)
SLOT_MINUTES = 30           # randomness granularity (30 mins)


def minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def should_post_now(now: datetime, seed: str) -> bool:
    # Only Mondays (0) and Fridays (4) in Adelaide local time
    if now.weekday() not in (0, 4):
        return False

    # Only within 09:00–17:00 local
    local_time = now.time()
    if not (WINDOW_START <= local_time < WINDOW_END):
        return False

    start_m = minutes_since_midnight(WINDOW_START)
    end_m = minutes_since_midnight(WINDOW_END)
    now_m = minutes_since_midnight(local_time)

    # Allowed slots: 09:00, 09:30, ... 16:30
    slots = list(range(start_m, end_m, SLOT_MINUTES))
    if not slots:
        return False

    # Pick one deterministic "random" slot per local date
    date_str = now.date().isoformat()  # Adelaide local date
    h = hashlib.sha256((seed + "|" + date_str).encode("utf-8")).digest()
    chosen_index = int.from_bytes(h[:4], "big") % len(slots)
    chosen_m = slots[chosen_index]

    # Post only if we're exactly at the chosen slot boundary
    return now_m == chosen_m


def load_random_quote() -> str:
    with open("quotes.txt", "r", encoding="utf-8") as f:
        quotes = [q.strip() for q in f if q.strip()]
    if not quotes:
        raise RuntimeError("quotes.txt is empty")
    return random.choice(quotes)


def main() -> None:
    seed = os.environ.get("SCHEDULE_SEED", "default-seed")
    now = datetime.now(ADELAIDE).replace(second=0, microsecond=0)

    if not should_post_now(now, seed):
        print(f"Not posting. Adelaide now: {now.isoformat()}")
        return

    quote = load_random_quote()

    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(
        channel=os.environ["SLACK_CHANNEL"],
        text=f"Quote of the day:\n> {quote}"
    )
    print(f"Posted. Adelaide now: {now.isoformat()}")


if __name__ == "__main__":
    main()
