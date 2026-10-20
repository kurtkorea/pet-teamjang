FROM peti-mvp-ai-worker:latest
WORKDIR /app
RUN pip install --no-cache-dir onvif-zeep==0.2.12
COPY app.py .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
