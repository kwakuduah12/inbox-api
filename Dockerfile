FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY inbox_api/ inbox_api/
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "inbox_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
