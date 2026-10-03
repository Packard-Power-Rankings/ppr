FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG REQUIREMENTS_FILE=requirements.txt

COPY requirements*.txt ./
COPY docker-entrypoint.sh /usr/local/bin/ppr-entrypoint

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r "${REQUIREMENTS_FILE}" && \
    groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --create-home app && \
    mkdir -p /var/lib/ppr-archives /var/lib/ppr-uploads && \
    chown app:app /var/lib/ppr-archives /var/lib/ppr-uploads && \
    chmod 0755 /usr/local/bin/ppr-entrypoint

COPY --chown=app:app . .

ENV PYTHONPATH=/app

ENTRYPOINT ["ppr-entrypoint"]

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
