"""
matcher.py
Scores each new job against your resume using the Groq API.
Returns jobs with a 0-100 relevance score and a one-line reason,
filtered to a minimum threshold.
"""

import json
import os
from groq import Groq

MODEL = "llama-3.3-70b-versatile"
MIN_SCORE = int(os.environ.get("MIN_MATCH_SCORE", "60"))

RESUME_PATH = os.path.join(os.path.dirname(__file__), "resume.txt")


def load_resume():
    with open(RESUME_PATH, "r") as f:
        return f.read()


def score_job(client, resume_text, job):
    prompt = f"""You are screening a job posting against a candidate's resume for relevance.

RESUME:
{resume_text}

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description'][:3000]}

Score how relevant this job is to the candidate from 0-100, where:
- 90-100: Near-perfect match (e.g. Forward Deployed Engineer, AI Implementation Consultant, Solutions Engineer at an AI-native company)
- 70-89: Strong match, clearly relevant skill/domain overlap
- 50-69: Partial match, some transferable skills but different core function
- Below 50: Not a good fit

Respond with ONLY valid JSON, no markdown fences, no preamble:
{{"score": <int>, "reason": "<one sentence, under 20 words, explaining the score>"}}
"""
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content.strip()
    text = text.replace("\`\`\`json", "").replace("\`\`\`", "").strip()
    try:
        result = json.loads(text)
        return int(result.get("score", 0)), result.get("reason", "")
    except (json.JSONDecodeError, ValueError):
        return 0, "Could not parse match score."


def filter_relevant_jobs(jobs):
    """Takes raw new-job dicts, returns only those scoring >= MIN_SCORE,
    each annotated with 'score' and 'reason'."""
    if not jobs:
        return []

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set.")

    client = Groq(api_key=api_key)
    resume_text = load_resume()

    matched = []
    for job in jobs:
        score, reason = score_job(client, resume_text, job)
        job["score"] = score
        job["reason"] = reason
        if score >= MIN_SCORE:
            matched.append(job)
        print(f"  scored {job['company']} / {job['title']}: {score} - {reason}")

    matched.sort(key=lambda j: j["score"], reverse=True)
    return matched
