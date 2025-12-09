FROM python:3.13-slim

WORKDIR /app

COPY shared /shared
RUN pip install --no-cache-dir /shared

COPY inventory_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY inventory_service/app ./app

EXPOSE 9004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9004"]
