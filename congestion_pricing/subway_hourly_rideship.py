import os
import time
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://data.ny.gov/resource/5wq4-mkjj.json"

# Optional but recommended if you make many requests:
APP_TOKEN = None  # e.g. "YOUR_SOCRATA_APP_TOKEN"

# Pagination
PAGE_SIZE = 50000
offset = 0

# Output
OUT_CSV = "mta_daily_station_ridership_by_station_id.csv"

# Your working query shape (using Socrata backticks as in the data viewer)
BASE_QUERY = (
    "SELECT "
    "`station_complex_id`, "
    "sum(`ridership`) AS daily_ridership, "
    "date_trunc_ymd(`transit_timestamp`) AS by_day_transit_timestamp "
    "WHERE caseless_one_of(`transit_mode`, \"subway\") "
    "GROUP BY `station_complex_id`, date_trunc_ymd(`transit_timestamp`) "
    "ORDER BY by_day_transit_timestamp, `station_complex_id`"
)

def make_session(app_token=None):
    s = requests.Session()

    # Retry on transient errors + timeouts
    retry = Retry(
        total=8,
        connect=8,
        read=8,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount("https://", adapter)
    s.mount("http://", adapter)

    if app_token:
        s.headers.update({"X-App-Token": app_token})

    return s

session = make_session(APP_TOKEN)

# If file exists, resume by counting rows already written (optional resume)
if os.path.exists(OUT_CSV):
    existing_rows = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8")) - 1  # minus header
    if existing_rows > 0:
        offset = (existing_rows // PAGE_SIZE) * PAGE_SIZE
        print(f"Found existing {existing_rows:,} rows in {OUT_CSV}. Resuming at offset={offset}.")

first_write = not os.path.exists(OUT_CSV)

while True:
    paged_query = f"{BASE_QUERY} LIMIT {PAGE_SIZE} OFFSET {offset}"

    try:
        r = session.get(
            BASE_URL,
            params={"$query": paged_query},
            timeout=(30, 240),  # (connect timeout, read timeout)
        )
    except requests.exceptions.ReadTimeout:
        # Extra backoff on top of urllib3 retries, just in case
        print("ReadTimeout hit; sleeping 10s and retrying same page...")
        time.sleep(10)
        continue

    # If still not OK, show body and stop (you can restart; it will resume)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}\nURL: {r.url}\nResponse:\n{r.text}")

    batch = r.json()
    if not batch:
        print("No more rows; done.")
        break

    df = pd.DataFrame(batch)

    # Normalize types/column names
    df.rename(columns={"by_day_transit_timestamp": "service_date"}, inplace=True)
    df["service_date"] = pd.to_datetime(df["service_date"]).dt.date
    df["daily_ridership"] = pd.to_numeric(df["daily_ridership"], errors="coerce").fillna(0).astype(int)

    # Append to CSV incrementally
    df.to_csv(OUT_CSV, mode="a", index=False, header=first_write)
    first_write = False

    offset += PAGE_SIZE
    print(f"Wrote {len(df):,} rows (next offset={offset})")

print(f"Saved: {OUT_CSV}")
