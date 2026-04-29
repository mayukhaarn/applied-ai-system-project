# fi.co Homework Review Dashboard

This repository now includes a GitHub Pages-ready static interface at `index.html`.
The page is designed to let you enter a founder name and email, display the relevant review data, and "send" reviewed homework from the browser.

## What is included

- `index.html` — static dashboard for GitHub Pages
- `README.md` — documentation and deployment instructions
- Existing `fi_*.py` modules are untouched and remain in the repo

## How the page works

1. Enter founder name and email.
2. If the founder exists in the sample dataset, the review fields populate automatically.
3. If the founder is not found, fill in the review fields manually.
4. The preview updates automatically.
5. Click **Send reviewed homework** to mark the review as ready to send.

## Sample founder data included

- `Alex Johnson` — `alex@startup.com`
- `Priya Patel` — `priya@greenflow.co`

## Deploying on GitHub Pages

1. Commit `index.html` to the repository.
2. In your GitHub repo settings, enable GitHub Pages.
3. Set the source to the `main` branch and root (`/`).
4. The page will be available at `https://mayukhaarn.github.io/applied-ai-system-project/`.

## Limitations

- This is a static page and does not send actual emails.
- The review workflow is a front-end prototype to demonstrate the user flow.
- For real email delivery, a backend service is required.

## Local preview

You can preview the page locally by opening `index.html` in a browser, or run a simple local server:

```bash
python3 -m http.server 8000
```

Then navigate to:

```text
http://localhost:8000/index.html
```

## Suggested next steps

- Connect the static dashboard to a backend API for real data lookup.
- Wire the "Send reviewed homework" button to an email service.
- Add an actual founder roster and homework submission database.

## Influence and comparison

This codebase is influenced by the modular, agent-style architecture found in the BugHound starter repository at `https://github.com/mayukhaarn/ai110-module5tinker-bughound-starter`.

### Shared architectural ideas

- Modular components that separate retrieval, reasoning, and evaluation.
- A workflow that chains together a context retriever, a decision-making agent, and a validation/evaluator stage.
- A human-in-the-loop mindset: the evaluator flags uncertain or risky outputs for manual review.
- A focus on a clean pipeline rather than a single monolithic script.

### Key differences

- This repository is built around a homework tracking and review workflow for `fi.co`, not a Python bug repair assistant.
- It uses `fi_*` scraper, grading, sheets, and email modules, whereas BugHound focuses on code analysis, LLM-based fix generation, and risk scoring.
- The current repo includes a static GitHub Pages demo UI in `index.html`; BugHound uses a Streamlit app and a more interactive debugging experience.
- This project is domain-specific to founder homework grading and reporting, while BugHound is a reusable tool for analyzing and patching Python snippets.
- The external repo also places more emphasis on offline heuristics, reliability tests, and model fallback handling; this repo currently emphasizes integration with Google Sheets, email delivery, and a sample front-end prototype.

### Why this matters

The influence is conceptual rather than literal: the current project borrows the idea of a staged pipeline and review guardrails, but it is adapted to a different problem space and a different deployment style.
