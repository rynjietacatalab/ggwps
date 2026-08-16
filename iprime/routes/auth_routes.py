"""
routes/auth_routes.py
----------------------
Every URL the app responds to, grouped in one Blueprint.

Flow:
  /register        -> create an account (starts unverified), email an OTP
  /verify-email     -> check that OTP once, mark the account verified
  /resend-otp       -> send a fresh code if the first one is lost/expired
  /login             -> username OR email + password. No OTP here — the
                         email was already proven once, at registration.
  /dashboard        -> only reachable once logged in
  /logout           -> clear the session
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.user import create_user, get_user_by_identifier, verify_password, mark_email_verified
from utils.otp_utils import generate_otp, save_otp, verify_otp
from utils.email_utils import send_otp_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Fill in every field to continue.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Those passwords don't match.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Use at least 6 characters for your password.", "error")
            return render_template("register.html")

        success, message = create_user(username, email, password)
        if not success:
            flash(message, "error")
            return render_template("register.html")

        # The one and only OTP in this app: sent right after account
        # creation, to prove the email address is real.
        otp_code = generate_otp()
        save_otp(email, otp_code)
        sent, msg = send_otp_email(email, otp_code, username)

        session["pending_user"] = username
        session["pending_email"] = email.strip().lower()

        if sent:
            flash("Account created. Enter the code we emailed you to activate it.", "success")
        else:
            flash(f"Account created, but the code couldn't be emailed: {msg}", "error")

        return redirect(url_for("auth.verify_email"))

    return render_template("register.html")


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    if "pending_email" not in session:
        return redirect(url_for("auth.login"))

    masked_email = _mask_email(session["pending_email"])

    if request.method == "POST":
        submitted_otp = request.form.get("otp", "")
        ok, message = verify_otp(session["pending_email"], submitted_otp)

        if ok:
            mark_email_verified(session["pending_email"])
            session.pop("pending_user", None)
            session.pop("pending_email", None)
            flash("Your email is verified. Sign in to continue.", "success")
            return redirect(url_for("auth.login"))

        flash(message, "error")
        return render_template("verify_email.html", masked_email=masked_email)

    return render_template("verify_email.html", masked_email=masked_email)


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    if "pending_email" not in session:
        return redirect(url_for("auth.login"))

    email = session["pending_email"]
    username = session.get("pending_user", "")

    otp_code = generate_otp()
    save_otp(email, otp_code)
    sent, msg = send_otp_email(email, otp_code, username)

    flash("We sent a fresh code." if sent else msg, "success" if sent else "error")
    return redirect(url_for("auth.verify_email"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")

        user = get_user_by_identifier(identifier)
        if not user or not verify_password(identifier, password):
            flash("That username/email or password isn't right.", "error")
            return render_template("login.html")

        if not user["email_verified"]:
            # They created an account but never finished the one-time
            # email check — send them to finish that, not back through
            # a second OTP later.
            session["pending_user"] = user["username"]
            session["pending_email"] = user["email"]
            flash("Verify your email before signing in.", "error")
            return redirect(url_for("auth.verify_email"))

        session["logged_in"] = True
        session["username"] = user["username"]
        flash("Welcome back.", "success")
        return redirect(url_for("auth.dashboard"))

    return render_template("login.html")


@auth_bp.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", username=session.get("username"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))


def _mask_email(email):
    """user@example.com -> u***@example.com, for display only."""
    try:
        name, domain = email.split("@", 1)
        if len(name) <= 1:
            return email
        return f"{name[0]}{'*' * (len(name) - 1)}@{domain}"
    except ValueError:
        return email
