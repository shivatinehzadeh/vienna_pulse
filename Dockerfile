FROM python:3.13.3 AS base
WORKDIR /vienna_pulse

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000


FROM base AS production
CMD ["bash", "-c", "python uvicorn setup.base:app --host 0.0.0.0 --port 8000"]

