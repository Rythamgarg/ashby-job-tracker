"""
main.py
Orchestrates: scrape Ashby boards -> filter by location -> score
relevance against resume -> email digest -> mark jobs as seen.

Run daily via cron or GitHub Actions.
"""

from scraper import get_new_relevant_jobs, mark_jobs_seen
from matcher import filter_relevant_jobs
from mailer import send_digest


def main():
    print("Fetching new job postings from Ashby boards...")
    new_jobs = get_new_relevant_jobs()
    print(f"Found {len(new_jobs)} new location-relevant job(s). Scoring against resume...")

    matched_jobs = filter_relevant_jobs(new_jobs)
    print(f"{len(matched_jobs)} job(s) passed the relevance threshold.")

    try:
        send_digest(matched_jobs)
    except Exception as e:
        print(f"[warn] Failed to send email: {e}")
        print("Continuing to mark jobs as seen...")

    # Mark ALL fetched jobs (matched or not) as seen so we don't
    # re-score low-relevance postings every day.
    mark_jobs_seen(new_jobs)
    print("Done.")


if __name__ == "__main__":
    main()
