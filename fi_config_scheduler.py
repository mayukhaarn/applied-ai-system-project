"""
config.py — Load all secrets from environment variables (never hardcode credentials).

Copy .env.example → .env and fill in your values.
Install: pip install python-dotenv
"""

# config.py
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # fi.co admin credentials
    "FI_EMAIL":           os.environ["FI_EMAIL"],
    "FI_PASSWORD":        os.environ["FI_PASSWORD"],

    # Anthropic (for grading + feedback generation)
    "ANTHROPIC_API_KEY":  os.environ["ANTHROPIC_API_KEY"],

    # Google Sheets
    "GOOGLE_SHEET_ID":    os.environ["GOOGLE_SHEET_ID"],   # from the sheet URL
    "GOOGLE_CREDS_JSON":  os.environ.get("GOOGLE_CREDS_JSON", "credentials.json"),

    # Email — SendGrid (preferred) OR SMTP
    "SENDGRID_API_KEY":   os.environ.get("SENDGRID_API_KEY", ""),
    "FROM_EMAIL":         os.environ.get("FROM_EMAIL", "program@fi.co"),
    "SMTP_HOST":          os.environ.get("SMTP_HOST", ""),
    "SMTP_PORT":          os.environ.get("SMTP_PORT", "465"),
    "SMTP_USER":          os.environ.get("SMTP_USER", ""),
    "SMTP_PASS":          os.environ.get("SMTP_PASS", ""),

    # Recipients — add as many director/PA emails as needed
    "DIRECTOR_EMAILS": [
        e.strip() for e in os.environ.get("DIRECTOR_EMAILS", "").split(",") if e.strip()
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# scheduler.py — runs the workflow on a cron-like schedule
# Run with: python scheduler.py
# ─────────────────────────────────────────────────────────────────────────────

"""
scheduler.py
"""

import schedule, time, logging
from main import run_scrape_and_grade, run_weekly_digest, run_feedback

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def safe(fn):
    def wrapper():
        try:
            fn()
        except Exception as e:
            log.error(f"Scheduled job failed: {e}", exc_info=True)
    return wrapper


if __name__ == "__main__":
    # Scrape + grade every day at 06:00
    schedule.every().day.at("06:00").do(safe(run_scrape_and_grade))

    # Saturday at 09:00 → send weekly digest to directors/PAs
    schedule.every().saturday.at("09:00").do(safe(run_weekly_digest))

    # After each scrape, send individual feedback (Stage 2) at 07:00
    schedule.every().day.at("07:00").do(safe(run_feedback))

    log.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)
