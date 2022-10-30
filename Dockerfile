FROM python:3.8.15-alpine3.16
WORKDIR /app
COPY app.py .
COPY schedule_0.json .
COPY schedule_1.json .
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY templates templates
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 CMD curl -f http://localhost:5000/health || exit 1
ENTRYPOINT ["python", "app.py"]