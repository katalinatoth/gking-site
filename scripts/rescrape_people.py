#!/usr/bin/env python3
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content', 'people')
BASE_URL = 'https://gking.harvard.edu/people/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

slugs = sorted(os.listdir(CONTENT_DIR))
print(f"Found {len(slugs)} people directories")

updated = 0
for i, slug in enumerate(slugs):
    decoded_slug = unquote(slug)
    url = BASE_URL + decoded_slug
    md_path = os.path.join(CONTENT_DIR, slug, 'index.md')

    if not os.path.exists(md_path):
        continue

    print(f"[{i+1}/{len(slugs)}] {decoded_slug}...", end=" ", flush=True)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Get professional title
        title_el = soup.select_one('.field--name-field-hwp-person-prof-title')
        prof_title = title_el.get_text().strip() if title_el else ''

        # Get bio from hwp-body
        bio_el = soup.select_one('.field--name-field-hwp-body')
        bio_html = bio_el.decode_contents().strip() if bio_el else ''

        # Get website link
        website_el = soup.select_one('.field--name-field-person-website a')
        if not website_el:
            website_el = soup.select_one('a[href*="website"]')
        website = ''
        if website_el and website_el.get('href'):
            href = website_el.get('href')
            if href.startswith('http'):
                website = href

        # Get email
        email_el = soup.select_one('.field--name-field-person-email a')
        email = ''
        if email_el and email_el.get('href', '').startswith('mailto:'):
            email = email_el.get('href').replace('mailto:', '')

        # Read existing md to get current title
        with open(md_path, 'r') as f:
            existing = f.read()

        # Extract the title from existing front matter
        page_title = decoded_slug.replace('-', ' ').title()
        for line in existing.split('\n'):
            if line.startswith('title:'):
                page_title = line.split(':', 1)[1].strip().strip('"')
                break

        # Build new content
        role_line = f'role: "{prof_title}"' if prof_title else ''
        
        lines = ['---', f'title: "{page_title}"', 'type: "people"']
        if role_line:
            lines.append(role_line)
        lines.append('---')
        lines.append('')

        # Build body content
        body_parts = []
        if bio_html:
            body_parts.append(bio_html)

        contact_parts = []
        if website:
            contact_parts.append(f'**Website:** [{website}]({website})')
        if email:
            contact_parts.append(f'**Email:** [{email}](mailto:{email})')

        if contact_parts:
            body_parts.append('\n'.join(contact_parts))

        if not body_parts:
            body_parts.append('Member of Gary King\'s research group.')

        body = '\n\n'.join(body_parts)
        lines.append(body)
        lines.append('')

        new_content = '\n'.join(lines)

        if new_content != existing:
            with open(md_path, 'w') as f:
                f.write(new_content)
            updated += 1
            status = []
            if prof_title:
                status.append(f'title="{prof_title[:40]}"')
            if bio_html:
                status.append(f'bio={len(bio_html)}')
            if website:
                status.append('website')
            if email:
                status.append('email')
            print(' | '.join(status) if status else 'no new info')
        else:
            print('unchanged')

    except Exception as e:
        print(f"ERROR: {e}")

    if (i + 1) % 10 == 0:
        time.sleep(0.5)

print(f"\nDone. Updated {updated}/{len(slugs)} people pages.")
