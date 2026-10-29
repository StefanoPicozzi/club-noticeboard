"""Club noticeboard: committee members post notices, everyone else reads them."""
import hmac
import os
import secrets
import sqlite3
from datetime import datetime

from flask import Flask, abort, redirect, render_template_string, request, session, url_for


def setting(name, default=None):
    """Read a setting from NAME, or from the file NAME_FILE points at."""
    path = os.environ.get(f"{name}_FILE")
    if path:
        with open(path) as f:
            return f.read().strip()
    return os.environ.get(name, default)


ADMIN_PASSWORD = setting("ADMIN_PASSWORD")
SECRET_KEY = setting("SECRET_KEY")
for name, value in (("ADMIN_PASSWORD", ADMIN_PASSWORD), ("SECRET_KEY", SECRET_KEY)):
    if not value:
        raise SystemExit(f"{name} (or {name}_FILE) must be set; see README.md")

DB = os.environ.get("DB_PATH", "/app/data/notices.db")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Served over HTTPS in production; set SESSION_COOKIE_SECURE=0 to try it on plain http://localhost.
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "1") != "0",
)

PAGE = """
<!doctype html>
<title>{{ club }} noticeboard</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; color: #222; }
  article { border-bottom: 1px solid #ddd; padding: 1rem 0; }
  small { color: #777; }
  form { display: grid; gap: .5rem; margin: 1rem 0; }
  input, textarea { font: inherit; padding: .4rem; }
</style>
<h1>{{ club }} noticeboard</h1>
{% for n in notices %}
  <article>
    <h2>{{ n["title"] }}</h2>
    <p>{{ n["body"] }}</p>
    <small>{{ n["posted"] }}</small>
    {% if admin %}<form method="post" action="/delete/{{ n['id'] }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button>Delete</button></form>{% endif %}
  </article>
{% else %}
  <p>Nothing posted yet.</p>
{% endfor %}
{% if admin %}
  <h2>New notice</h2>
  <form method="post" action="/new">
    <input type="hidden" name="csrf" value="{{ csrf }}">
    <input name="title" placeholder="Title" required>
    <textarea name="body" placeholder="Details" rows="4"></textarea>
    <button>Post</button>
  </form>
  <p><a href="/logout">Log out</a></p>
{% else %}
  <p><small><a href="/login">Committee login</a></small></p>
{% endif %}
"""

LOGIN = """
<!doctype html><title>Committee login</title>
<h1>Committee login</h1>
{% if error %}<p style="color:#b00">{{ error }}</p>{% endif %}
<form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
<input type="password" name="password" placeholder="Password" autofocus>
<button>Log in</button></form>
"""


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("create table if not exists notices (id integer primary key, title text, body text, posted text)")
    return con


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf", "")
        if not session.get("csrf") or not hmac.compare_digest(sent, session["csrf"]):
            abort(400)


@app.route("/healthz")
def healthz():
    with db() as con:
        con.execute("select 1")
    return "ok"


@app.route("/")
def index():
    with db() as con:
        notices = con.execute("select * from notices order by id desc").fetchall()
    return render_template_string(PAGE, notices=notices, admin=session.get("admin"), csrf=csrf_token(),
                                  club=os.environ.get("CLUB_NAME", "Our club"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", "").encode(), ADMIN_PASSWORD.encode()):
            session.clear()
            session["admin"] = True
            return redirect(url_for("index"))
        error = "Wrong password."
    return render_template_string(LOGIN, error=error, csrf=csrf_token())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/new", methods=["POST"])
def new():
    if not session.get("admin"):
        return redirect(url_for("login"))
    with db() as con:
        con.execute("insert into notices (title, body, posted) values (?, ?, ?)",
                    (request.form["title"], request.form.get("body", ""), datetime.now().strftime("%d %b %Y, %H:%M")))
    return redirect(url_for("index"))


@app.route("/delete/<int:notice_id>", methods=["POST"])
def delete(notice_id):
    if session.get("admin"):
        with db() as con:
            con.execute("delete from notices where id = ?", (notice_id,))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
