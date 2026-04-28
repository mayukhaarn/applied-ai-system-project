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
4. The page will be available at `https://<your-username>.github.io/<repo-name>/`.

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
