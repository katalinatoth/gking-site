# Google Indexing API — Bulk URL Submitter

Submits all real gking.harvard.edu pages to Google's Indexing API for
priority re-crawling. This accelerates the migration from old Drupal URLs
to new Hugo URLs in Google's index (hours instead of months).

## Setup (One-Time)

### Step 1: Create a Google Cloud Project

1. Open https://console.cloud.google.com/ in your browser
2. Sign in with the Google account that has access to the gking.harvard.edu Search Console property
3. At the top of the page, click **"Select a project"** (or it may say "Create or select a project")
4. Click **"New Project"** in the top-right of the popup
5. In the "Project name" field, type `gking-indexing`
6. If it asks for an Organization/Parent resource, select `harvard.edu` and click **Browse** to pick any available folder
7. Click **"Create"**
8. Wait a few seconds, then make sure `gking-indexing` is shown as the active project in the top bar

### Step 2: Enable the Indexing API

1. In the search bar at the top of the page, type `Web Search Indexing API`
2. Click the result that says **"Web Search Indexing API"**
3. Click the blue **"Enable"** button
4. Wait for it to finish enabling (you'll see a green checkmark or be taken to the API dashboard)

### Step 3: Enable the Search Console API

1. In the search bar at the top of the page, type `Google Search Console API`
2. Click the result that says **"Google Search Console API"**
3. Click the blue **"Enable"** button

### Step 4: Create a Service Account

1. In the search bar at the top of the page, type `Service Accounts`
2. Click the result that says **"Service Accounts"** (under IAM & Admin)
3. Click **"+ Create Service Account"** at the top of the page
4. In the "Service account name" field, type `gking-indexer`
5. Click **"Create and Continue"**
6. On the "Grant this service account access" screen, don't select anything — just click **"Continue"**
7. On the "Grant users access" screen, don't change anything — just click **"Done"**

### Step 5: Download the Key File

1. You should now see `gking-indexer` in the service accounts list — click on its email address
2. Click the **"Keys"** tab at the top
3. Click **"Add Key"**
4. Click **"Create new key"**
5. Make sure **"JSON"** is selected
6. Click **"Create"**
7. A `.json` file will automatically download to your computer
8. Move that file into this folder (`_automation/indexing/`) and rename it to `service-account-key.json`

### Step 6: Give the Service Account Access to Search Console

1. Open your terminal
2. Navigate to this folder:

```bash
cd _automation/indexing
```

3. Run this command:

```bash
python3 -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file(
    'service-account-key.json',
    scopes=['https://www.googleapis.com/auth/webmasters']
)
service = build('webmasters', 'v3', credentials=credentials)
service.sites().add(siteUrl='https://gking.harvard.edu/').execute()
print('Done! Service account linked to gking.harvard.edu')
"
```

4. You should see: `Done! Service account linked to gking.harvard.edu`

### Step 7: Install Python Dependencies

Run this in your terminal:

```bash
pip3 install google-auth google-auth-httplib2 google-api-python-client
```

---

## Daily Usage

Once setup is complete, run this command once per day for ~5 days:

```bash
cd _automation/indexing
python3 submit_urls.py --key service-account-key.json
```

Each run submits 200 URLs (Google's daily limit). After ~5 days, all 938 pages will be submitted.

### Check Progress

```bash
python3 submit_urls.py --key service-account-key.json --status
```

This shows how many URLs have been submitted, how many are remaining, and how many days are left.

### Retry Failed URLs

If some URLs failed during a run:

```bash
python3 submit_urls.py --key service-account-key.json --retry-failed
```

### Submit Fewer URLs Per Run

If you want to submit fewer than 200 at a time:

```bash
python3 submit_urls.py --key service-account-key.json --limit 50
```

---

## How It Works

- `urls.txt` contains 938 real page URLs extracted from the Hugo sitemap (excludes author stubs and other non-user-facing pages)
- The script submits 200 URLs/day (Google's quota limit)
- Progress is saved in `submitted_urls.json` — safe to interrupt and resume
- Google's quota resets at **midnight Pacific Time** (3 AM Eastern)
- Google typically indexes submitted pages within 1–24 hours of submission

## Files

| File | Purpose |
|------|---------|
| `submit_urls.py` | The submission script |
| `urls.txt` | All 938 URLs to submit |
| `submitted_urls.json` | Auto-generated progress tracker (created on first run) |
| `service-account-key.json` | Your service account key — **DO NOT commit to git** |
| `README.md` | This file |

## Important Notes

- **Never commit the service account key file to git.** It contains private credentials.
- The API quota resets daily at **midnight Pacific Time**.
- If you see "Quota exceeded" errors, just wait until tomorrow and run again.
- If you see "Permission denied" errors, re-run the Step 6 command above.
- Pages typically appear in Google search results within 24–48 hours of submission.
