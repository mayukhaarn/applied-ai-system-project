"""
SheetsManager — reads and writes to a Google Sheet with four tabs:
  📋 Active Founders   — all current founders + grades
  📬 Submissions       — per-homework detailed grading
  🚪 Dropped Founders  — founders who left the cohort
  📊 Summary           — cohort-level stats for the digest

Install: pip install gspread google-auth
"""

import gspread, logging
from datetime import datetime
from google.oauth2.service_account import Credentials

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet tab names
TAB_ACTIVE    = "Active Founders"
TAB_SUBMITTED = "Submissions"
TAB_DROPPED   = "Dropped Founders"
TAB_SUMMARY   = "Summary"


class SheetsManager:
    def __init__(self, sheet_id: str, creds_json: str):
        creds        = Credentials.from_service_account_file(creds_json, scopes=SCOPES)
        gc           = gspread.authorize(creds)
        self.wb      = gc.open_by_key(sheet_id)
        self._ensure_tabs()

    # ── Tab bootstrap ─────────────────────────────────────────────────────────
    def _ensure_tabs(self):
        existing = {ws.title for ws in self.wb.worksheets()}
        for name, headers in [
            (TAB_ACTIVE,    ["ID","Name","Email","Company","Team ID","Submitted","Completeness","Effort","Originality","Total","Grade","AI Likely","Summary","Last Updated"]),
            (TAB_SUBMITTED, ["ID","Name","Email","Company","Hw Week","Submitted","Completeness","Effort","Originality","Total","Grade","AI Likely","Summary","Strengths","Improvements","Feedback Sent","Last Updated"]),
            (TAB_DROPPED,   ["ID","Name","Email","Company","Dropped Date","Reason","Notes"]),
            (TAB_SUMMARY,   ["Week","Total Active","Submitted","Not Submitted","Avg Score","Avg Completeness","Avg Effort","Avg Originality","Drop Count","Generated"]),
        ]:
            if name not in existing:
                ws = self.wb.add_worksheet(title=name, rows=500, cols=len(headers)+2)
                ws.append_row(headers, value_input_option="USER_ENTERED")
                self._format_header(ws)
                log.info(f"Created tab: {name}")

    def _format_header(self, ws):
        ws.format("1:1", {"textFormat": {"bold": True}, "backgroundColor": {"red":0.2,"green":0.2,"blue":0.6}})

    def _ws(self, name: str):
        return self.wb.worksheet(name)

    # ── Active Founders tab ──────────────────────────────────────────────────
    def update_tracker(self, results: list[dict]):
        ws   = self._ws(TAB_ACTIVE)
        rows = ws.get_all_records()
        id_to_row = {str(r["ID"]): i+2 for i, r in enumerate(rows)}  # 1-indexed, +1 header
        now  = datetime.now().strftime("%Y-%m-%d %H:%M")

        updates = []
        new_rows = []
        for r in results:
            fid  = str(r.get("id",""))
            row  = [
                fid,
                r.get("name",""),
                r.get("email",""),
                r.get("company",""),
                r.get("team_id",""),
                "✓" if r.get("submitted") else "✗",
                r.get("completeness",0),
                r.get("effort",0),
                r.get("originality",0),
                r.get("total",0),
                r.get("letter_grade",""),
                "Yes" if r.get("ai_likely") else "No",
                r.get("summary",""),
                now,
            ]
            if fid in id_to_row:
                ws.update(f"A{id_to_row[fid]}:N{id_to_row[fid]}", [row])
            else:
                new_rows.append(row)

        if new_rows:
            ws.append_rows(new_rows, value_input_option="USER_ENTERED")

        self._update_summary(results)
        log.info(f"Active tab updated ({len(results)} founders)")

    # ── Dropped Founders tab ─────────────────────────────────────────────────
    def mark_dropped(self, founders: list[dict]):
        ws_active  = self._ws(TAB_ACTIVE)
        ws_dropped = self._ws(TAB_DROPPED)
        all_active = ws_active.get_all_records()

        for f in founders:
            fid = str(f.get("id",""))
            # Add to Dropped tab
            ws_dropped.append_row([
                fid,
                f.get("name",""),
                f.get("email",""),
                f.get("company",""),
                f.get("dropped_date", datetime.today().strftime("%Y-%m-%d")),
                f.get("dropped_reason",""),
                f.get("notes",""),
            ], value_input_option="USER_ENTERED")

            # Remove from Active tab
            for i, row in enumerate(all_active):
                if str(row.get("ID")) == fid:
                    ws_active.delete_rows(i+2)
                    break

        log.info(f"Marked {len(founders)} as dropped")

    # ── Summary tab ──────────────────────────────────────────────────────────
    def _update_summary(self, results: list[dict]):
        ws   = self._ws(TAB_SUMMARY)
        week = datetime.now().strftime("%Y-W%U")
        submitted = [r for r in results if r.get("submitted")]
        dropped_ws = self._ws(TAB_DROPPED)
        drop_count = max(0, len(dropped_ws.get_all_records()))

        def avg(key):
            vals = [r.get(key,0) for r in submitted]
            return round(sum(vals)/len(vals),1) if vals else 0

        row = [
            week,
            len(results),
            len(submitted),
            len(results) - len(submitted),
            avg("total"),
            avg("completeness"),
            avg("effort"),
            avg("originality"),
            drop_count,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ]
        # Check if week already exists and update, else append
        records = ws.get_all_records()
        for i, r in enumerate(records):
            if r.get("Week") == week:
                ws.update(f"A{i+2}:J{i+2}", [row])
                return
        ws.append_row(row, value_input_option="USER_ENTERED")

    # ── Getters ──────────────────────────────────────────────────────────────
    def get_active_founders(self) -> list[dict]:
        return self._ws(TAB_ACTIVE).get_all_records()

    def get_all_data(self) -> dict:
        return {
            "active":   self._ws(TAB_ACTIVE).get_all_records(),
            "dropped":  self._ws(TAB_DROPPED).get_all_records(),
            "summary":  self._ws(TAB_SUMMARY).get_all_records(),
        }

    def get_graded_submissions(self) -> list[dict]:
        return self._ws(TAB_ACTIVE).get_all_records()

    def mark_feedback_sent(self, founder_id: str):
        ws   = self._ws(TAB_SUBMITTED)
        rows = ws.get_all_records()
        for i, r in enumerate(rows):
            if str(r.get("ID")) == str(founder_id):
                ws.update_cell(i+2, 16, "✓")  # col 16 = Feedback Sent
                break
