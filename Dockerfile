FROM python:3.13-slim
RUN pip install --no-cache-dir uvicorn stac-fastapi-geoparquet
CMD ["uvicorn", "stac_fastapi.geoparquet.main:app"]
