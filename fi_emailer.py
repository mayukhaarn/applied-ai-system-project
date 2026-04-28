"""
Emailer — two classes:
  DigestEmailer   → weekly Saturday digest to directors/PAs
  FeedbackEmailer → personalised feedback to individual founders (Stage 2)

Uses SendGrid (recommended) or falls back to smtplib.
Install: pip install sendgrid
"""

import smtplib, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime             import datetime

log = logging.getLogger(__name__)


# ── HTML Templates ─────────────────────────────────────────────────────────────

DIGEST_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: -apple-system, sans-serif; color:#1a1a1a; margin:0; padding:0; background:#f5f5f5; }}
  .container {{ max-width:700px; margin:24px auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.1); }}
  .header {{ background:#1e1e3f; color:#fff; padding:28px 32px; }}
  .header h1 {{ margin:0; font-size:22px; }}
  .header p  {{ margin:6px 0 0; opacity:.7; font-size:14px; }}
  .stats {{ display:flex; gap:12px; padding:20px 32px; background:#f8f8ff; border-bottom:1px solid #eee; flex-wrap:wrap; }}
  .stat {{ flex:1; min-width:120px; background:#fff; border-radius:8px; padding:14px; text-align:center; border:1px solid #e8e8f0; }}
  .stat .num {{ font-size:28px; font-weight:700; color:#1e1e3f; }}
  .stat .lbl {{ font-size:12px; color:#888; margin-top:4px; }}
  .section {{ padding:20px 32px; }}
  .section h2 {{ font-size:16px; color:#1e1e3f; border-bottom:2px solid #e8e8f0; padding-bottom:8px; margin-top:0; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ background:#f0f0fa; text-align:left; padding:8px 10px; color:#555; font-weight:600; }}
  td {{ padding:8px 10px; border-bottom:1px solid #f0f0f0; }}
  tr:hover td {{ background:#fafafe; }}
  .badge {{ display:inline-block; border-radius:4px; padding:2px 7px; font-size:11px; font-weight:600; }}
  .badge-ok {{ background:#d4edda; color:#155724; }}
  .badge-miss {{ background:#f8d7da; color:#721c24; }}
  .badge-drop {{ background:#fff3cd; color:#856404; }}
  .badge-ai   {{ background:#e2d9f3; color:#432874; }}
  .grade-A {{ color:#155724; font-weight:700; }}
  .grade-B {{ color:#004085; font-weight:700; }}
  .grade-C {{ color:#856404; font-weight:700; }}
  .grade-D {{ color:#721c24; font-weight:700; }}
  .footer {{ padding:16px 32px; background:#f8f8ff; text-align:center; font-size:11px; color:#999; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚀 fi.co Cohort Homework Digest</h1>
    <p>Week of {week_label} &nbsp;·&nbsp; Generated {generated}</p>
  </div>

  <div class="stats">
    <div class="stat"><div class="num">{total_active}</div><div class="lbl">Active Founders</div></div>
    <div class="stat"><div class="num" style="color:#155724">{submitted}</div><div class="lbl">Submitted</div></div>
    <div class="stat"><div class="num" style="color:#721c24">{not_submitted}</div><div class="lbl">Missing</div></div>
    <div class="stat"><div class="num">{avg_score}</div><div class="lbl">Avg Score /30</div></div>
    <div class="stat"><div class="num" style="color:#856404">{drop_count}</div><div class="lbl">Dropped</div></div>
  </div>

  <!-- SUBMITTED -->
  <div class="section">
    <h2>✅ Submitted ({submitted})</h2>
    <table>
      <tr><th>Founder</th><th>Company</th><th>Grade</th><th>Score</th><th>Completeness</th><th>Effort</th><th>Originality</th><th>AI?</th></tr>
      {submitted_rows}
    </table>
  </div>

  <!-- NOT SUBMITTED -->
  <div class="section">
    <h2>❌ Not Submitted ({not_submitted})</h2>
    <table>
      <tr><th>Founder</th><th>Company</th><th>Email</th></tr>
      {missing_rows}
    </table>
  </div>

  <!-- DROPPED -->
  {dropped_section}

  <div class="footer">
    fi.co Homework Tracker &nbsp;·&nbsp; Sent every Saturday &nbsp;·&nbsp; <a href="{sheet_url}">Open Google Sheet</a>
  </div>
</div>
</body>
</html>
"""

DROPPED_SECTION_HTML = """
  <div class="section">
    <h2>🚪 Dropped This Cohort ({drop_count})</h2>
    <table>
      <tr><th>Founder</th><th>Company</th><th>Date Dropped</th><th>Reason</th></tr>
      {dropped_rows}
    </table>
  </div>
"""

FEEDBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family:-apple-system,sans-serif; color:#1a1a1a; background:#f5f5f5; margin:0; padding:0; }}
  .container {{ max-width:600px; margin:24px auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.1); }}
  .header {{ background:#1e1e3f; color:#fff; padding:24px 28px; }}
  .header h1 {{ margin:0; font-size:20px; }}
  .scores {{ display:flex; gap:10px; padding:16px 28px; background:#f8f8ff; flex-wrap:wrap; }}
  .score {{ flex:1; min-width:100px; text-align:center; background:#fff; border-radius:8px; padding:10px; border:1px solid #e8e8f0; }}
  .score .num {{ font-size:24px; font-weight:700; color:#1e1e3f; }}
  .score .lbl {{ font-size:11px; color:#888; }}
  .body {{ padding:20px 28px; line-height:1.7; }}
  .grade-box {{ display:inline-block; background:#1e1e3f; color:#fff; border-radius:8px; padding:6px 18px; font-size:28px; font-weight:700; float:right; margin-top:-8px; }}
  .footer {{ padding:14px 28px; background:#f8f8ff; font-size:11px; color:#999; text-align:center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Homework Feedback — {name}</h1>
  </div>
  <div class="scores">
    <div class="score"><div class="num">{completeness}/10</div><div class="lbl">Completeness</div></div>
    <div class="score"><div class="num">{effort}/10</div><div class="lbl">Effort</div></div>
    <div class="score"><div class="num">{originality}/10</div><div class="lbl">Originality</div></div>
    <div class="score"><div class="num">{total}/30</div><div class="lbl">Total</div></div>
    <div class="score"><div class="num">{letter_grade}</div><div class="lbl">Grade</div></div>
  </div>
  <div class="body">
    {feedback_body}
    {ai_notice}
  </div>
  <div class="footer">fi.co Program Team · Reply to this email with any questions</div>
</div>
</body>
</html>
"""

AI_NOTICE = """
<p style="background:#fef3cd;border-radius:6px;padding:10px 14px;font-size:13px;color:#856404;">
  <strong>⚠️ Note:</strong> Our system detected that portions of your submission may be AI-generated.
  We encourage your authentic voice — the prompts are designed to draw out <em>your</em> specific experience and insights.
  Please reach out if you have questions about our AI use policy.
</p>
"""


# ── Email helpers ──────────────────────────────────────────────────────────────

def _send_email(cfg: dict, to: list[str], subject: str, html: str):
    """Try SendGrid first, fall back to SMTP."""
    if cfg.get("SENDGRID_API_KEY"):
        _send_sendgrid(cfg, to, subject, html)
    else:
        _send_smtp(cfg, to, subject, html)

def _send_sendgrid(cfg, to, subject, html):
    import sendgrid
    from sendgrid.helpers.mail import Mail
    sg  = sendgrid.SendGridAPIClient(api_key=cfg["SENDGRID_API_KEY"])
    msg = Mail(
        from_email    = cfg["FROM_EMAIL"],
        to_emails     = to,
        subject       = subject,
        html_content  = html,
    )
    r = sg.send(msg)
    log.info(f"SendGrid → {to} | status {r.status_code}")

def _send_smtp(cfg, to, subject, html):
    msg                    = MIMEMultipart("alternative")
    msg["Subject"]         = subject
    msg["From"]            = cfg["FROM_EMAIL"]
    msg["To"]              = ", ".join(to)
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], int(cfg.get("SMTP_PORT", 465))) as s:
        s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.sendmail(cfg["FROM_EMAIL"], to, msg.as_string())
    log.info(f"SMTP → {to}")


# ── DigestEmailer ──────────────────────────────────────────────────────────────

class DigestEmailer:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def send_digest(self, data: dict, recipients: list[str]):
        active  = data.get("active",  [])
        dropped = data.get("dropped", [])
        summary = data.get("summary", [{}])[-1]  # latest row

        submitted    = [r for r in active if r.get("Submitted") == "✓"]
        not_submitted= [r for r in active if r.get("Submitted") != "✓"]

        submitted_rows = "".join(
            f"<tr>"
            f"<td>{r['Name']}</td>"
            f"<td>{r['Company']}</td>"
            f"<td class='grade-{r.get('Grade','?')[0]}'>{r.get('Grade','?')}</td>"
            f"<td>{r.get('Total',0)}</td>"
            f"<td>{r.get('Completeness',0)}/10</td>"
            f"<td>{r.get('Effort',0)}/10</td>"
            f"<td>{r.get('Originality',0)}/10</td>"
            f"<td>{'<span class=badge badge-ai>Yes</span>' if r.get('AI Likely')=='Yes' else '—'}</td>"
            f"</tr>"
            for r in sorted(submitted, key=lambda x: -int(x.get("Total",0)))
        )

        missing_rows = "".join(
            f"<tr><td>{r['Name']}</td><td>{r['Company']}</td>"
            f"<td><a href='mailto:{r['Email']}'>{r['Email']}</a></td></tr>"
            for r in not_submitted
        )

        if dropped:
            dropped_rows = "".join(
                f"<tr><td>{r['Name']}</td><td>{r['Company']}</td>"
                f"<td>{r.get('Dropped Date','')}</td><td>{r.get('Reason','')}</td></tr>"
                for r in dropped
            )
            dropped_section = DROPPED_SECTION_HTML.format(
                drop_count=len(dropped), dropped_rows=dropped_rows
            )
        else:
            dropped_section = ""

        html = DIGEST_HTML.format(
            week_label    = datetime.now().strftime("%B %d, %Y"),
            generated     = datetime.now().strftime("%Y-%m-%d %H:%M"),
            total_active  = len(active),
            submitted     = len(submitted),
            not_submitted = len(not_submitted),
            avg_score     = summary.get("Avg Score", "—"),
            drop_count    = len(dropped),
            submitted_rows= submitted_rows,
            missing_rows  = missing_rows,
            dropped_section=dropped_section,
            sheet_url     = f"https://docs.google.com/spreadsheets/d/{self.cfg['GOOGLE_SHEET_ID']}",
        )

        subject = f"[fi.co] Homework Digest – {datetime.now().strftime('%b %d')}"
        _send_email(self.cfg, recipients, subject, html)
        log.info(f"Digest sent to {recipients}")


# ── FeedbackEmailer (Stage 2) ──────────────────────────────────────────────────

class FeedbackEmailer:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def send_feedback(self, to_email: str, name: str, feedback_text: str, row: dict):
        # Convert plain text paragraphs to <p> tags
        body_html = "\n".join(f"<p>{p.strip()}</p>" for p in feedback_text.split("\n\n") if p.strip())

        html = FEEDBACK_HTML.format(
            name          = name,
            completeness  = row.get("completeness", row.get("Completeness", "—")),
            effort        = row.get("effort",        row.get("Effort", "—")),
            originality   = row.get("originality",   row.get("Originality", "—")),
            total         = row.get("total",         row.get("Total", "—")),
            letter_grade  = row.get("letter_grade",  row.get("Grade", "—")),
            feedback_body = body_html,
            ai_notice     = AI_NOTICE if row.get("ai_likely") or row.get("AI Likely") == "Yes" else "",
        )

        subject = f"Your fi.co Homework Feedback — {name}"
        _send_email(self.cfg, [to_email], subject, html)
        log.info(f"Feedback sent → {to_email}")
