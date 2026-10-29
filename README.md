# Club noticeboard

A small noticeboard for a club or a committee. Members read the notices; the committee logs in to post and delete them.

Built with Flask and SQLite.

## Run it

```bash
docker build -t club-noticeboard .
docker run -p 5000:5000 --env-file .env club-noticeboard
```

Then open http://localhost:5000. Log in at /login with the committee password.

## Settings

Put them in `.env`:

- `ADMIN_PASSWORD`: the committee password
- `CLUB_NAME`: the name shown at the top
