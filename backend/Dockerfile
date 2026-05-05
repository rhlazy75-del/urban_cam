FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/upload_2cam
VOLUME ["/app/upload_2cam"]

EXPOSE 5000
CMD ["uvicorn", "server2cam:app", "--host", "0.0.0.0", "--port", "5000"]
