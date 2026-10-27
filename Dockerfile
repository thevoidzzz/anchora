FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
EXPOSE 8000
ENTRYPOINT ["python", "-m", "anchora.api"]

FROM runtime AS tests
COPY tests ./tests
RUN pip install --no-cache-dir ".[dev]" && rm -rf src
ENTRYPOINT ["pytest"]
CMD ["-q"]
