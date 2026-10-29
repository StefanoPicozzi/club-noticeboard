"""Club noticeboard: committee members post notices, everyone else reads them."""
import os
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
DB = os.environ.get("DB_PATH", "/app/data/notices.db")

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
    {% if admin %}<form method="post" action="/delete/{{ n['id'] }}"><button>Delete</button></form>{% endif %}
  </article>
{% else %}
  <p>Nothing posted yet.</p>
{% endfor %}
{% if admin %}
  <h2>New notice</h2>
  <form method="post" action="/new">
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
<form method="post"><input type="password" name="password" placeholder="Password" autofocus>
<button>Log in</button></form>
"""


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("create table if not exists notices (id integer primary key, title text, body text, posted text)")
    return con


@app.route("/")
def index():
    with db() as con:
        notices = con.execute("select * from notices order by id desc").fetchall()
    return render_template_string(PAGE, notices=notices, admin=session.get("admin"),
                                  club=os.environ.get("CLUB_NAME", "Our club"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("index"))
        error = "Wrong password."
    return render_template_string(LOGIN, error=error)


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
