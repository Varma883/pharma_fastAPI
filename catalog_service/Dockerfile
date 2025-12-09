FROM python:3.13-slim

WORKDIR /app

COPY shared /shared
RUN pip install --no-cache-dir /shared

COPY catalog_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY catalog_service/app ./app

EXPOSE 9002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9002"]
