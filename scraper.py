"""
scraper.py
Fetches job postings from Ashby's public Job Board API for a list of
company board slugs, filters for target locations, and returns only
jobs not seen in a previous run.
"""

import json
import os
import requests

ASHBY_API_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

# Keywords used to decide if a job's location counts as "relevant" to you.
# Edit this list freely.
LOCATION_KEYWORDS = [
    "dubai", "uae", "u.a.e", "abu dhabi", "united arab emirates",
    "mena", "middle east", "remote",
]

SEEN_JOBS_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")


def load_companies(path="companies.json"):
    with open(path, "r") as f:
        return json.load(f)


def load_seen_jobs():
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    with open(SEEN_JOBS_FILE, "r") as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()


def save_seen_jobs(seen_ids):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def is_location_relevant(location: str) -> bool:
    if not location:
        return False
    loc = location.lower()
    return any(kw in loc for kw in LOCATION_KEYWORDS)


def fetch_jobs_for_company(slug: str):
    """Returns a list of job dicts for one company board, or [] on failure."""
    url = ASHBY_API_URL.format(slug=slug)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"[warn] {slug}: HTTP {resp.status_code} (bad slug or no public board)")
            return []
        data = resp.json()
        return data.get("jobs", [])
    except requests.RequestException as e:
        print(f"[warn] {slug}: request failed ({e})")
        return []


def get_new_relevant_jobs(companies_path="companies.json"):
    """
    Main entry point: fetches all companies' postings, filters to
    location-relevant + previously-unseen jobs, and returns them.
    Does NOT mark jobs as seen -- call mark_jobs_seen() after
    successfully emailing, so a failed email run retries next time.
    """
    companies = load_companies(companies_path)
    seen_ids = load_seen_jobs()
    new_jobs = []

    for slug in companies:
        jobs = fetch_jobs_for_company(slug)
        for job in jobs:
            job_id = job.get("id")
            if not job_id or job_id in seen_ids:
                continue
            location = job.get("location", "") or job.get("employmentType", "")
            # Ashby jobs also carry addresses under job.get("address", {})
            addr = job.get("address", {}) or {}
            full_location = " ".join(
                filter(None, [
                    location,
                    addr.get("postalAddress", {}).get("addressLocality", "") if isinstance(addr.get("postalAddress"), dict) else "",
                    addr.get("postalAddress", {}).get("addressCountry", "") if isinstance(addr.get("postalAddress"), dict) else "",
                ])
            )
            if not is_location_relevant(full_location):
                continue
            new_jobs.append({
                "id": job_id,
                "company": slug,
                "title": job.get("title", "Untitled role"),
                "location": full_location or "Not specified",
                "department": job.get("department", ""),
                "url": job.get("jobUrl", ""),
                "published_at": job.get("publishedAt", ""),
                "description": job.get("descriptionPlain", "") or "",
            })

    return new_jobs


def mark_jobs_seen(jobs):
    seen_ids = load_seen_jobs()
    for job in jobs:
        seen_ids.add(job["id"])
    save_seen_jobs(seen_ids)


if __name__ == "__main__":
    jobs = get_new_relevant_jobs()
    print(f"Found {len(jobs)} new relevant job(s).")
    for j in jobs:
        print(f"- [{j['company']}] {j['title']} ({j['location']})")
