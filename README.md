# Club noticeboard

A small noticeboard for a club or a committee. Members read the notices; the committee logs in to post and delete them.

Built with Flask and SQLite.

## Run it

Make the secrets on the machine, once. They never go in git:

```bash
mkdir -m 700 secrets
python3 -c "import secrets; print(secrets.token_urlsafe(18))" > secrets/admin_password
python3 -c "import secrets; print(secrets.token_hex(32))" > secrets/secret_key
chmod 644 secrets/*          # the container's user reads them; the folder stays private
cp .env.example .env         # then set CLUB_NAME
docker compose up -d --build
```

Then open http://localhost:5000 (on plain http, also set `SESSION_COOKIE_SECURE=0`, or the login will not stick). Log in at /login with the committee password: `cat secrets/admin_password`.

## Settings

- `ADMIN_PASSWORD` or `ADMIN_PASSWORD_FILE`: the committee password. Required.
- `SECRET_KEY` or `SECRET_KEY_FILE`: signs the login cookie. Required; long and random.
- `CLUB_NAME`: the name shown at the top.
- `DB_PATH`: where the notices live (default `/app/data/notices.db`).
- `SESSION_COOKIE_SECURE`: `1` (default) sends the login cookie over HTTPS only.

The app listens on port 5000 and keeps its data in `/app/data`, a volume.

## Back up

Everything is in the `/app/data` volume (one SQLite file). With Compose:

```bash
docker compose exec noticeboard python -c "import sqlite3; sqlite3.connect('/app/data/notices.db').backup(sqlite3.connect('/app/data/backup.db'))"
docker compose cp noticeboard:/app/data/backup.db ./notices-backup.db
```

To restore, stop the app, copy the file back to `/app/data/notices.db`, and start it.
