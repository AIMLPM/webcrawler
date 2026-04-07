# Benchmark environment for MarkCrawl head-to-head comparison.
#
# Bundles Python, Go, Playwright browsers, and all 7 benchmark tools so
# results are reproducible across machines.
#
# Build:
#   docker build -t markcrawl-bench -f benchmarks/Dockerfile .
#
# Run (pass API keys for firecrawl / answer-quality benchmarks):
#   docker run --rm \
#     -e FIRECRAWL_API_KEY \
#     -e OPENAI_API_KEY \
#     -v $(pwd)/benchmarks:/app/benchmarks \
#     markcrawl-bench python benchmarks/benchmark_all_tools.py
#
# The volume mount lets results write back to your host.

FROM python:3.13-slim AS base

# System deps for Playwright browsers and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget curl gnupg ca-certificates \
        # Playwright system deps (Chromium)
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
        libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
        libasound2 libwayland-client0 \
        # lxml build deps
        libxml2-dev libxslt1-dev \
        # General
        git \
    && rm -rf /var/lib/apt/lists/*

# ---------- Go (for Colly binary) ----------
FROM base AS go-builder
ARG GO_VERSION=1.24.4
RUN wget -q "https://go.dev/dl/go${GO_VERSION}.linux-$(dpkg --print-architecture).tar.gz" -O /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

COPY benchmarks/colly_crawler /build/colly_crawler
WORKDIR /build/colly_crawler
RUN go build -o colly_crawler .

# ---------- Final image ----------
FROM base

WORKDIR /app

# Copy the Go binary from builder
COPY --from=go-builder /build/colly_crawler/colly_crawler /app/benchmarks/colly_crawler/colly_crawler

# Install Python packages
COPY pyproject.toml README.md ./
COPY markcrawl/ markcrawl/
RUN pip install --no-cache-dir -e ".[js]"

# Benchmark tool dependencies
RUN pip install --no-cache-dir \
        scrapy \
        crawl4ai \
        "crawlee[playwright]" \
        firecrawl-py \
        python-dotenv \
        psutil \
        openai \
        numpy \
        rank_bm25 \
        sentence-transformers

# Install Playwright Chromium browser
RUN python -m playwright install chromium

# Copy benchmark scripts
COPY benchmarks/ benchmarks/

# Default: run the head-to-head comparison
ENTRYPOINT ["python", "benchmarks/benchmark_all_tools.py"]
