FROM python:3.12.16-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd --system --uid 10001 noticeboard && mkdir -p /app/data && chown noticeboard /app/data
USER noticeboard
VOLUME /app/data
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz')"
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
