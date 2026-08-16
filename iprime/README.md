# iPrime

A Flask login system for a health-monitoring app, backed by Neon
(Postgres) with one-time email verification at sign-up only — after
that, logging in just needs a username/email + password.

## Folder layout

```
iprime/
├── main.py               # entry point ONLY — builds the app, inits tables, registers routes
├── config.py              # all settings, read from environment variables
├── Procfile                # tells Render how to start the app (gunicorn)
├── render.yaml             # optional Render Blueprint
├── routes/
│   └── auth_routes.py      # every URL: /register /verify-email /login /dashboard ...
├── utils/
│   ├── otp_utils.py        # generate / store / check the verification code (in Neon)
│   └── email_utils.py      # the ONLY file that talks to Gmail's SMTP server
├── models/
│   ├── db.py                # the ONLY file that opens a connection to Neon
│   └── user.py              # user queries: create, look up, verify password
├── templates/                # HTML pages (Jinja2)
└── static/css/style.css      # the nude / latte / dirty-white theme
```

If something breaks, this tells you where to look: wrong page → routes/,
email never arrives → utils/email_utils.py, a code won't verify →
utils/otp_utils.py, anything database-shaped → models/.

## How sign-up and sign-in work

1. **Register** — username, email, password. The account is created but
   marked unverified, and a 6-digit code is emailed once.
2. **Verify email** — enter that code. This is the *only* time an OTP is
   used. Once verified, the account stays verified.
3. **Log in** — username **or** email + password. No code, every time —
   just a normal login, since the email was already proven at step 2.

If someone tries to log in before finishing step 2, they're sent back
to the verification page (with a "resend code" button) instead of
being asked to register again.

## 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Set up Neon

1. In your Neon project's dashboard, open **Connection Details** and
   copy the connection string (it already includes `sslmode=require`).
2. That's it — you don't need to create any tables by hand. The app
   creates `users` and `email_otps` itself the first time it starts.

## 3. Get a Gmail "App Password"

1. Turn on 2-Step Verification on the Gmail account you'll send from:
   https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords and create one
   (name it anything, e.g. "iPrime"). Copy the 16-character code shown.

## 4. Configure your secrets

```bash
cp .env.example .env
```

Fill in `SECRET_KEY`, `DATABASE_URL` (from Neon), `EMAIL_ADDRESS`, and
`EMAIL_APP_PASSWORD` in `.env`.

## 5. Run it locally

```bash
python main.py
```

Visit `http://127.0.0.1:5000`.

---

## Deploying to Render from GitHub — yes, even while it's experimental

Nothing about Render or GitHub cares whether a project is finished.
People deploy work-in-progress apps to Render constantly, either on a
private repo or just accepting that it's a rough build behind a
not-widely-shared URL. The steps:

1. **Push this folder to a GitHub repo.** Private is fine if you'd
   rather keep it out of public view while it's experimental.
2. **In Render:** New → Web Service → connect that repo.
3. **Build command:** `pip install -r requirements.txt`
   **Start command:** `gunicorn main:app` (Render may pick this up
   automatically from the Procfile).
4. **Add environment variables** in Render's Environment tab:
   `SECRET_KEY`, `DATABASE_URL` (your Neon string), `EMAIL_ADDRESS`,
   `EMAIL_APP_PASSWORD`. Don't commit `.env` — this is the equivalent
   step for production.
5. Deploy. Every future push to the connected branch redeploys
   automatically.

A couple of things worth knowing going in:

- **Render's free web service tier sleeps after inactivity** and takes
  roughly a minute to wake back up on the next request. Fine for an
  experimental/staging build; annoying for real users, so keep that in
  mind if you invite people to try it. Paid tiers remove this.
- **Real emails go out the moment it's live** — the Gmail account you
  configured will actually send verification codes to whatever address
  someone registers with, so anyone who finds the URL and signs up
  gets a real email. That's normal, just worth being aware of before
  sharing the link.
- Because the verification code is stored in Neon (not memory), a free
  tier "spin down" between registering and entering the code won't
  invalidate it — that was the whole reason to move it out of memory
  in the first place.
- If this ever handles real patient health data rather than the
  placeholder dashboard here, that's a different compliance
  conversation (data handling, access controls, etc.) than deploying
  a demo — worth keeping in mind as it grows past the experimental
  stage.

## Notes

- Passwords are always hashed (Werkzeug) — never stored in plain text.
- `app.run(debug=True)` only runs when you execute `python main.py`
  directly; Render runs the app through `gunicorn` instead (see
  Procfile), which never has debug mode on.
