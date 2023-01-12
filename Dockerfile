FROM python:3.8.15-alpine3.16
WORKDIR /app
COPY app.py .
COPY schedule_0.json .
COPY schedule_1.json .
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY templates templates
ENTRYPOINT ["python", "app.py"]