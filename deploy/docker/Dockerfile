FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY requirements-optional.txt /app/requirements-optional.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8765
EXPOSE 8787

CMD ["python", "scripts/scheduler.py"]
