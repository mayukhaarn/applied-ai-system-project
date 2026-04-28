"""
fi.co Homework Tracker — Agentic Workflow
=========================================
Stage 1: Scrape fi.co/admin/teams → grade homework → write to Google Sheets → email weekly digest
Stage 2: Send personalized feedback to individual founders

Run:
    python main.py --mode scrape        # scrape + grade + update sheet
    python main.py --mode digest        # send Saturday weekly digest
    python main.py --mode feedback      # send individual feedback (Stage 2)
    python main.py --mode mark-dropped  # interactively mark founders as dropped
"""

import argparse
from scraper      import FiScraper
from grader       import HomeworkGrader
from sheets       import SheetsManager
from emailer      import DigestEmailer, FeedbackEmailer
from config       import CONFIG
import logging, json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def run_scrape_and_grade():
    log.info("=== Stage 1: Scrape → Grade → Sheet ===")

    scraper  = FiScraper(CONFIG["FI_EMAIL"], CONFIG["FI_PASSWORD"])
    grader   = HomeworkGrader(CONFIG["ANTHROPIC_API_KEY"])
    sheets   = SheetsManager(CONFIG["GOOGLE_SHEET_ID"], CONFIG["GOOGLE_CREDS_JSON"])

    # 1. Pull all founders in the active cohort
    founders = scraper.get_cohort_founders()
    log.info(f"Found {len(founders)} founders in cohort")

    # 2. Pull homework submissions
    submissions = scraper.get_homework_submissions()

    # 3. Grade each submission
    results = []
    for founder in founders:
        sub = submissions.get(founder["id"])
        if sub:
            grade = grader.grade(sub)
        else:
            grade = {"submitted": False, "completeness": 0, "effort": 0, "originality": 0, "total": 0, "summary": "Not submitted"}
        results.append({**founder, **grade, "submitted": bool(sub)})

    # 4. Write to Google Sheets
    sheets.update_tracker(results)
    log.info("Sheet updated ✓")


def run_mark_dropped():
    """Interactive CLI to mark founders as dropped."""
    sheets = SheetsManager(CONFIG["GOOGLE_SHEET_ID"], CONFIG["GOOGLE_CREDS_JSON"])
    founders = sheets.get_active_founders()

    print("\n=== Mark Founders as Dropped ===")
    print("Type founder name or email, blank line to finish.\n")
    dropped = []
    while True:
        entry = input("Founder (name/email): ").strip()
        if not entry:
            break
        match = next((f for f in founders if entry.lower() in (f["name"]+f["email"]).lower()), None)
        if match:
            reason = input(f"  Reason for {match['name']} dropping: ").strip()
            dropped.append({**match, "dropped_reason": reason, "dropped_date": datetime.today().strftime("%Y-%m-%d")})
            print(f"  ✓ Queued: {match['name']}")
        else:
            print(f"  ✗ Not found: {entry}")

    if dropped:
        sheets.mark_dropped(dropped)
        log.info(f"Marked {len(dropped)} founder(s) as dropped ✓")


def run_weekly_digest():
    log.info("=== Sending Weekly Digest ===")
    sheets  = SheetsManager(CONFIG["GOOGLE_SHEET_ID"], CONFIG["GOOGLE_CREDS_JSON"])
    emailer = DigestEmailer(CONFIG)
    data    = sheets.get_all_data()
    emailer.send_digest(data, CONFIG["DIRECTOR_EMAILS"])
    log.info("Digest sent ✓")


def run_feedback():
    log.info("=== Stage 2: Sending Individual Feedback ===")
    sheets   = SheetsManager(CONFIG["GOOGLE_SHEET_ID"], CONFIG["GOOGLE_CREDS_JSON"])
    grader   = HomeworkGrader(CONFIG["ANTHROPIC_API_KEY"])
    emailer  = FeedbackEmailer(CONFIG)
    results  = sheets.get_graded_submissions()

    for row in results:
        if row.get("feedback_sent"):
            continue
        feedback = grader.generate_feedback(row)
        emailer.send_feedback(row["email"], row["name"], feedback, row)
        sheets.mark_feedback_sent(row["id"])
        log.info(f"  Feedback sent → {row['email']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scrape","digest","feedback","mark-dropped"], required=True)
    args = parser.parse_args()

    if   args.mode == "scrape":       run_scrape_and_grade()
    elif args.mode == "mark-dropped": run_mark_dropped()
    elif args.mode == "digest":       run_weekly_digest()
    elif args.mode == "feedback":     run_feedback()
