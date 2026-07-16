# Ashby Job Tracker

Daily-scrapes Ashby-hosted job boards for new postings relevant to
Rytham's profile (Forward Deployed Engineer / AI Implementation /
Solutions roles, Dubai/UAE/remote), scores them against a resume using
the Claude API, and emails a digest of only the new, relevant matches.

## How it works
1. `scraper.py` hits Ashby's public Job Board API
   (`https://api.ashbyhq.com/posting-api/job-board/{company-slug}`) for
   every company slug in `companies.json`, filters to Dubai/UAE/MENA/
   remote locations, and skips jobs already seen (tracked in
   `seen_jobs.json`).
2. `matcher.py` sends each new job + your resume to Claude, which
   returns a 0-100 relevance score and a one-line reason. Only jobs
   scoring >= `MIN_MATCH_SCORE` (default 60) are kept.
3. `mailer.py` emails you a digest of the matched jobs.
4. `main.py` runs all three in order and updates `seen_jobs.json`.

## One-time setup

### 1. Get the code running locally first (recommended before automating)
```bash
cd ashby-job-tracker
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env` and fill in:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `SMTP_USER` / `SMTP_PASS` — see Gmail setup below
- `MAIL_TO` — where you want the digest sent

Then load the env vars and do a test run:
```bash
export $(cat .env | xargs)
python main.py
```
You should see console output listing scraped jobs, their scores, and
(if any match) an email arriving in your inbox.

### 2. Gmail App Password (if using Gmail for sending)
1. Enable 2-Step Verification on your Google account.
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail" and use the 16-character code
   as `SMTP_PASS` (not your normal Gmail password).

### 3. Fix up `companies.json`
The slugs currently in there are my best guesses at company Ashby
board names — some may be wrong (Ashby slugs don't always match the
public brand name). To verify/find a company's real slug:
- Visit their careers page and look for a link to `jobs.ashbyhq.com/...`
- The last part of that URL is the slug.
Add/remove companies freely — one slug per line in the JSON array.

### 4. Automate with GitHub Actions (no server needed)
1. Push this folder to a new **private** GitHub repo.
2. In the repo, go to Settings → Secrets and variables → Actions, and
   add these repository secrets:
   - `ANTHROPIC_API_KEY`
   - `SMTP_HOST` (e.g. `smtp.gmail.com`)
   - `SMTP_PORT` (e.g. `587`)
   - `SMTP_USER`
   - `SMTP_PASS`
   - `MAIL_TO`
3. That's it — `.github/workflows/daily-job-check.yml` is already set
   up to run every day at 06:00 UTC (~10 AM Dubai time), and can also
   be triggered manually from the Actions tab ("Run workflow").
4. The workflow commits the updated `seen_jobs.json` back to the repo
   after each run, so dedup state persists between days.

### 5. Alternative: local cron (if you'd rather not use GitHub Actions)
```bash
crontab -e
# add this line (adjust path):
0 8 * * * cd /path/to/ashby-job-tracker && export $(cat .env | xargs) && /usr/bin/python3 main.py >> run.log 2>&1
```

## Tuning relevance matching
- Edit `resume.txt` any time your target roles/skills change — the
  matcher reads it fresh every run.
- Adjust `MIN_MATCH_SCORE` in `.env` (or the GitHub secret) to be
  stricter (e.g. 75) or looser (e.g. 45).
- Edit `LOCATION_KEYWORDS` in `scraper.py` to widen/narrow the
  location filter.

## Notes
- Ashby's Job Board API is public and requires no authentication —
  it's the same data that powers `jobs.ashbyhq.com/{slug}` pages.
- Not every company uses Ashby. This only catches postings from
  companies whose careers page is Ashby-hosted.
- Claude API calls cost a small amount per run (one call per new job
  found, using Claude Sonnet) — with a handful of new postings a day
  this is a negligible cost.
