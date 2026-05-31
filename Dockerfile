








# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Use the full image so we have gcc + Rust available for any compiled packages
FROM python:3.11-slim AS builder

# Install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (needed if pydantic-core falls back to source build)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

COPY requirements.txt .

# Install into a separate prefix so we can copy only the packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
# Slim final image — no Rust, no gcc, just Python + our packages
FROM python:3.11-slim AS runtime

# Don't write .pyc files; don't buffer stdout (logs appear instantly)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

EXPOSE 8080

CMD ["python", "main.py"]