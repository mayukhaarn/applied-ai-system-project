# ─── .env.example ────────────────────────────────────────────────────────────
# Copy this file to .env and fill in real values before running.

# fi.co admin login
FI_EMAIL=your_admin@fi.co
FI_PASSWORD=your_password

# Anthropic (get from https://console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-...

# Google Sheets
# 1. Create a new Google Sheet
# 2. Share it with your service account email (found in credentials.json)
# 3. Paste the Sheet ID from the URL:  /d/<SHEET_ID>/edit
GOOGLE_SHEET_ID=1BxiM...
GOOGLE_CREDS_JSON=credentials.json   # path to your service account JSON

# Email delivery — choose SendGrid OR SMTP
SENDGRID_API_KEY=SG.xxxx             # leave blank to use SMTP instead
FROM_EMAIL=program@yourorganization.com

# SMTP fallback (only needed if SENDGRID_API_KEY is blank)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=you@gmail.com
SMTP_PASS=your_app_password

# Comma-separated list of directors and program associates to receive digest
DIRECTOR_EMAILS=director@fi.co,associate@fi.co


# ─── README.md ────────────────────────────────────────────────────────────────

: '
# fi.co Homework Tracker

## Setup (5 minutes)

### 1. Install dependencies
pip install playwright gspread google-auth anthropic sendgrid \
            schedule python-dotenv
playwright install chromium

### 2. Google Service Account
1. Go to https://console.cloud.google.com → APIs & Services → Credentials
2. Create a Service Account → download JSON → save as `credentials.json`
3. Enable: Google Sheets API + Google Drive API
4. Create a new Google Sheet, share it with the service account email

### 5. Configure
cp .env.example .env
# Edit .env with your credentials

### 6. Run

# One-time: scrape all founders + grade homework + update sheet
python main.py --mode scrape

# Manually mark founders as dropped (interactive prompt)
python main.py --mode mark-dropped

# Send weekly digest now (normally runs Saturday 09:00)
python main.py --mode digest

# Send individual feedback to founders (Stage 2)
python main.py --mode feedback

# Run the full automated scheduler (runs 24/7)
python scheduler.py

## Google Sheet Structure
| Tab               | Contents                                       |
|-------------------|------------------------------------------------|
| Active Founders   | All current founders + grades                  |
| Submissions       | Per-homework detailed grading + feedback status|
| Dropped Founders  | Founders who left (name, date, reason)         |
| Summary           | Weekly cohort-level stats                      |

## Grading Rubric (0-10 each, total /30)
| Dimension   | What it measures                                      |
|-------------|-------------------------------------------------------|
| Completeness| Every sub-question answered                           |
| Effort      | Depth, specificity, examples, research                |
| Originality | Personal insight vs. generic AI output                |

## Stage 2: Individual Feedback
Run `python main.py --mode feedback` after reviewing grades.
Claude generates personalised emails referencing each founder's
specific scores and submission content.
'
