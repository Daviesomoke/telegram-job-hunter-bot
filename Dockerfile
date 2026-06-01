









# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl && rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local

# Copy all flat source files
COPY main.py config.py db.py base.py helpers.py \
     reddit.py rss.py job_pipeline.py user.py \
     scraper_remoteok.py scraper_himalayas.py scraper_lever.py ./

RUN mkdir -p /app/data

RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

EXPOSE 8080
CMD ["python", "main.py"]