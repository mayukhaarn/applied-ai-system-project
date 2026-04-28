"""
FiScraper — logs into fi.co/admin/teams, scrapes cohort founders
and homework submissions. Uses Playwright for JS-heavy pages.

Install: pip install playwright && playwright install chromium
"""

import re, time, json, logging
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)

BASE_URL  = "https://fi.co"
ADMIN_URL = f"{BASE_URL}/admin/teams"


class FiScraper:
    def __init__(self, email: str, password: str, headless: bool = True):
        self.email    = email
        self.password = password
        self.headless = headless
        self._page    = None
        self._pw      = None
        self._browser = None

    # ── Context manager support ──────────────────────────────────────────────
    def __enter__(self):
        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        ctx           = self._browser.new_context()
        self._page    = ctx.new_page()
        self._login()
        return self

    def __exit__(self, *_):
        self._browser.close()
        self._pw.stop()

    # Allow use without `with` statement
    def _ensure_open(self):
        if not self._page:
            self.__enter__()

    # ── Authentication ───────────────────────────────────────────────────────
    def _login(self):
        log.info("Logging in to fi.co …")
        self._page.goto(f"{BASE_URL}/login")
        self._page.wait_for_selector("input[type='email'], input[name='email']", timeout=15000)

        email_field = (
            self._page.query_selector("input[type='email']") or
            self._page.query_selector("input[name='email']")
        )
        pw_field = (
            self._page.query_selector("input[type='password']") or
            self._page.query_selector("input[name='password']")
        )
        email_field.fill(self.email)
        pw_field.fill(self.password)

        submit = (
            self._page.query_selector("button[type='submit']") or
            self._page.query_selector("input[type='submit']")
        )
        submit.click()

        # Wait for redirect away from /login
        self._page.wait_for_url(re.compile(r"^(?!.*\/login).*$"), timeout=20000)
        log.info("Login successful ✓")

    # ── Founder list ─────────────────────────────────────────────────────────
    def get_cohort_founders(self) -> list[dict]:
        """Returns list of dicts: {id, name, email, company, team_id}"""
        self._ensure_open()
        self._page.goto(ADMIN_URL)
        self._page.wait_for_load_state("networkidle")

        founders = []

        # Intercept the XHR/fetch that loads teams (common pattern on fi.co)
        # Fall back to DOM scraping if the API endpoint isn't easily interceptable
        try:
            founders = self._scrape_teams_via_api()
        except Exception as e:
            log.warning(f"API scrape failed ({e}), falling back to DOM scrape")
            founders = self._scrape_teams_via_dom()

        log.info(f"Scraped {len(founders)} founders")
        return founders

    def _scrape_teams_via_api(self) -> list[dict]:
        """Try to call the same JSON endpoint the admin UI calls."""
        resp = self._page.evaluate("""
            async () => {
                const r = await fetch('/api/admin/teams?cohort=active', {
                    headers: {'X-Requested-With': 'XMLHttpRequest',
                              'Accept': 'application/json'}
                });
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            }
        """)
        teams   = resp if isinstance(resp, list) else resp.get("teams", resp.get("data", []))
        founders = []
        for team in teams:
            members = team.get("members", team.get("founders", []))
            for m in members:
                founders.append({
                    "id":       m.get("id") or m.get("user_id"),
                    "name":     m.get("name") or m.get("full_name", ""),
                    "email":    m.get("email", ""),
                    "company":  team.get("name") or team.get("company_name", ""),
                    "team_id":  team.get("id"),
                })
        return founders

    def _scrape_teams_via_dom(self) -> list[dict]:
        """DOM fallback — adapt selectors to actual fi.co markup."""
        self._page.wait_for_selector(".team-row, tr[data-team-id], .founder-card", timeout=15000)
        rows = self._page.query_selector_all(".team-row, tr[data-team-id], .founder-card")
        founders = []
        for row in rows:
            text    = row.inner_text()
            email   = re.search(r"[\w.+-]+@[\w-]+\.\w+", text)
            founder = {
                "id":       row.get_attribute("data-user-id") or row.get_attribute("data-id"),
                "name":     self._extract(row, ".founder-name, .name, td:nth-child(1)"),
                "email":    email.group() if email else "",
                "company":  self._extract(row, ".company-name, .team-name, td:nth-child(2)"),
                "team_id":  row.get_attribute("data-team-id"),
            }
            if founder["name"] or founder["email"]:
                founders.append(founder)
        return founders

    def _extract(self, el, selector: str) -> str:
        node = el.query_selector(selector)
        return node.inner_text().strip() if node else ""

    # ── Homework submissions ─────────────────────────────────────────────────
    def get_homework_submissions(self) -> dict[str, dict]:
        """
        Returns {founder_id: {question_1: answer, question_2: answer, ...}}
        Navigates to each homework review page.
        """
        self._ensure_open()
        submissions = {}

        # Try API first
        try:
            raw = self._page.evaluate("""
                async () => {
                    const r = await fetch('/api/admin/homework/submissions', {
                        headers: {'Accept': 'application/json'}
                    });
                    if (!r.ok) throw new Error(r.status);
                    return r.json();
                }
            """)
            entries = raw if isinstance(raw, list) else raw.get("submissions", [])
            for s in entries:
                fid = str(s.get("founder_id") or s.get("user_id") or s.get("id"))
                submissions[fid] = s
        except Exception as e:
            log.warning(f"Submissions API failed ({e}), scraping individually")
            submissions = self._scrape_submissions_individually()

        log.info(f"Fetched {len(submissions)} homework submissions")
        return submissions

    def _scrape_submissions_individually(self) -> dict[str, dict]:
        """Navigate to each founder's submission page and scrape answers."""
        self._page.goto(f"{BASE_URL}/admin/homework")
        self._page.wait_for_load_state("networkidle")

        submission_links = self._page.query_selector_all("a[href*='/homework/'], a[href*='/submission/']")
        submissions = {}

        for link in submission_links:
            href = link.get_attribute("href")
            if not href:
                continue
            full_url = href if href.startswith("http") else BASE_URL + href
            self._page.goto(full_url)
            self._page.wait_for_load_state("networkidle")

            founder_id = re.search(r"/(\d+)", href)
            founder_id = founder_id.group(1) if founder_id else href

            # Extract Q&A pairs
            questions = self._page.query_selector_all(".question, .hw-question, [data-question]")
            answers   = self._page.query_selector_all(".answer, .hw-answer, [data-answer]")
            qa = {}
            for i, (q, a) in enumerate(zip(questions, answers), 1):
                qa[f"q{i}"]    = q.inner_text().strip()
                qa[f"a{i}"]    = a.inner_text().strip()
            qa["raw_page_text"] = self._page.inner_text("body")
            submissions[str(founder_id)] = qa

        return submissions

    # ── Contact info scrape (Stage 2) ────────────────────────────────────────
    def get_founder_contact_info(self, founder_id: str) -> dict:
        """Scrapes profile page for phone, LinkedIn, etc."""
        self._ensure_open()
        self._page.goto(f"{BASE_URL}/admin/founders/{founder_id}")
        self._page.wait_for_load_state("networkidle")
        text = self._page.inner_text("body")

        phone     = re.search(r"\+?[\d\s\-().]{10,}", text)
        linkedin  = re.search(r"linkedin\.com/in/[\w-]+", text)
        twitter   = re.search(r"twitter\.com/[\w]+", text)

        return {
            "founder_id": founder_id,
            "phone":      phone.group().strip()   if phone    else "",
            "linkedin":   linkedin.group()         if linkedin else "",
            "twitter":    twitter.group()          if twitter  else "",
        }
