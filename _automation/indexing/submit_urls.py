#!/usr/bin/env python3
"""
Google Indexing API Bulk Submitter for gking.harvard.edu

Submits URLs to Google's Indexing API to accelerate re-crawling
after the Drupal → Hugo migration. Processes 200 URLs/day (API limit).

Setup:
  1. Create a Google Cloud project and enable the "Indexing API"
  2. Create a Service Account and download the JSON key file
  3. Add the service account email as an Owner in Google Search Console
  4. pip install google-auth google-auth-httplib2 google-api-python-client
  5. Run: python submit_urls.py --key service-account-key.json

The script tracks progress in submitted_urls.json so it can resume
across days without re-submitting already-processed URLs.
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-auth google-auth-httplib2 google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/indexing"]
API_DAILY_LIMIT = 200
PROGRESS_FILE = Path(__file__).parent / "submitted_urls.json"
URLS_FILE = Path(__file__).parent / "urls.txt"


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"submitted": [], "failed": []}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def load_urls():
    if not URLS_FILE.exists():
        print(f"Error: {URLS_FILE} not found.")
        print("Generate it from the sitemap first.")
        sys.exit(1)
    return [line.strip() for line in URLS_FILE.read_text().splitlines() if line.strip()]


def submit_url(service, url, action="URL_UPDATED"):
    body = {"url": url, "type": action}
    try:
        response = service.urlNotifications().publish(body=body).execute()
        return True, response
    except HttpError as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Submit URLs to Google Indexing API")
    parser.add_argument("--key", required=True, help="Path to service account JSON key file")
    parser.add_argument("--limit", type=int, default=API_DAILY_LIMIT, help="Max URLs to submit this run (default: 200)")
    parser.add_argument("--status", action="store_true", help="Show progress status and exit")
    parser.add_argument("--retry-failed", action="store_true", help="Retry previously failed URLs")
    args = parser.parse_args()

    progress = load_progress()
    all_urls = load_urls()

    if args.status:
        submitted = set(progress["submitted"])
        remaining = [u for u in all_urls if u not in submitted]
        print(f"Total URLs:     {len(all_urls)}")
        print(f"Submitted:      {len(progress['submitted'])}")
        print(f"Failed:         {len(progress['failed'])}")
        print(f"Remaining:      {len(remaining)}")
        print(f"Days left:      {max(1, len(remaining) // API_DAILY_LIMIT)}")
        return

    credentials = service_account.Credentials.from_service_account_file(
        args.key, scopes=SCOPES
    )
    service = build("indexing", "v3", credentials=credentials)

    submitted_set = set(progress["submitted"])

    if args.retry_failed:
        urls_to_submit = progress["failed"][:args.limit]
        progress["failed"] = progress["failed"][len(urls_to_submit):]
    else:
        urls_to_submit = [u for u in all_urls if u not in submitted_set][:args.limit]

    if not urls_to_submit:
        print("All URLs have been submitted! Nothing to do.")
        return

    print(f"Submitting {len(urls_to_submit)} URLs (limit: {args.limit})...")
    print(f"Already submitted: {len(submitted_set)} / {len(all_urls)}")
    print()

    success_count = 0
    fail_count = 0

    for i, url in enumerate(urls_to_submit, 1):
        ok, response = submit_url(service, url)
        if ok:
            progress["submitted"].append(url)
            success_count += 1
            print(f"  [{i}/{len(urls_to_submit)}] ✓ {url}")
        else:
            progress["failed"].append(url)
            fail_count += 1
            print(f"  [{i}/{len(urls_to_submit)}] ✗ {url}")
            print(f"    Error: {response}")

        # Brief pause to avoid rate limiting
        if i % 10 == 0:
            time.sleep(1)

        # Save progress every 50 URLs
        if i % 50 == 0:
            save_progress(progress)

    save_progress(progress)

    print()
    print(f"Done! Submitted: {success_count}, Failed: {fail_count}")
    remaining = len(all_urls) - len(set(progress["submitted"]))
    if remaining > 0:
        print(f"Remaining: {remaining} URLs — run again tomorrow for the next batch.")


if __name__ == "__main__":
    main()
