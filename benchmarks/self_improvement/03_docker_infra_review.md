# Spec 03: Docker Infrastructure Review

**Scope:** Firecrawl Docker stack, main project Dockerfile, benchmarks
Dockerfile. Focuses on configuration, stability, and resource management.

**When to run:** After any Docker config change, after Firecrawl version
updates, or when investigating OOM/crash issues.

---

## Files in scope

| File | Purpose |
|------|---------|
| `Dockerfile` (project root) | Main markcrawl Docker image |
| `benchmarks/Dockerfile` | Benchmark environment with all tools |
| `benchmarks/firecrawl/firecrawl-src/docker-compose.yaml` | Firecrawl services (gitignored) |
| `benchmarks/firecrawl/firecrawl-src/.env` | Firecrawl environment vars (gitignored) |

---

## What to check

### 1. Firecrawl Docker stack stability

The Firecrawl stack has 5 services: API (with embedded workers), Playwright
service, Redis, RabbitMQ, and NuQ PostgreSQL. The main failure mode is OOM
in the Node.js workers.

**Resource limits:**

- [ ] `api` service `mem_limit` is sufficient (current: 12G)
- [ ] `playwright-service` `mem_limit` is set (current: 8G)
- [ ] `NODE_OPTIONS: "--max-old-space-size=<value>"` is set on the API service
- [ ] Worker count math checks out:
  ```
  NUQ_WORKER_COUNT workers + harness + extract-worker + other Node processes
  Total V8 heap = workers * max-old-space-size + overhead
  Must fit within api mem_limit
  ```

```bash
# Check current values
grep -n "mem_limit\|NODE_OPTIONS\|NUQ_WORKER_COUNT\|WORKER_COUNT" \
  benchmarks/firecrawl/firecrawl-src/docker-compose.yaml \
  benchmarks/firecrawl/firecrawl-src/.env
```

**Known OOM pattern:**
1. Worker receives large page (e.g., stripe-docs API reference)
2. V8 heap exceeds `max-old-space-size` -> process exits with code 134
3. Harness detects worker death -> kills ALL services
4. On restart, leftover jobs in NuQ PostgreSQL are picked up immediately
5. Workers OOM again on the same large pages -> crash loop

- [ ] Are leftover NuQ jobs cleaned on restart?
- [ ] Is there a way to skip known-bad URLs?

### 2. Firecrawl configuration (.env)

Check that `.env` values are conservative enough for stability:

| Variable | Current | Recommended | Why |
|----------|---------|-------------|-----|
| `NUM_WORKERS_PER_QUEUE` | 1 | 1 | One worker per queue prevents resource contention |
| `CRAWL_CONCURRENT_REQUESTS` | 1 | 1-3 | Higher values risk OOM on large pages |
| `MAX_CONCURRENT_JOBS` | 1 | 1 | Multiple jobs multiply memory pressure |
| `BROWSER_POOL_SIZE` | 2 | 2-3 | Each browser instance uses ~200-500 MB |
| `NUQ_WORKER_COUNT` | 2 | 2 | Must fit within container memory with V8 heap |

```bash
cat benchmarks/firecrawl/firecrawl-src/.env
```

### 3. Firecrawl restart behavior

- [ ] Does `docker compose down api && docker compose up -d api` work cleanly?
  - Note: `docker compose up -d api` alone does NOT restart an exited container
- [ ] Are RabbitMQ queues flushed on restart? (stale jobs cause OOM)
- [ ] Is PostgreSQL NuQ queue flushed on restart?

```bash
# Check if Firecrawl is running
docker compose -f benchmarks/firecrawl/firecrawl-src/docker-compose.yaml ps
# Check for leftover jobs (if running)
docker compose -f benchmarks/firecrawl/firecrawl-src/docker-compose.yaml \
  exec nuq-postgres psql -U postgres -c "SELECT count(*) FROM nuq.queue_scrape;"
```

### 4. Known Firecrawl limitations

These are architectural, not configuration bugs. Document them in reports:

| Site | Issue | Root Cause |
|------|-------|------------|
| react-dev | 43/221 pages (19%) | Self-hosted lacks `fire-engine` anti-bot bypass |
| stripe-docs | 395/402 (98%) | 7 pages exceed V8 heap on any config |
| wikipedia | Variable | Transient; depends on Docker resource pressure |

- [ ] Are these limitations accurately reflected in benchmark reports?
- [ ] Are the page counts in reports consistent with what Firecrawl actually returns?

### 5. Main project Dockerfile

```bash
cat Dockerfile
```

- [ ] Base image is pinned to a specific version (not `latest`)
- [ ] Multi-stage build (if applicable)
- [ ] Non-root user
- [ ] No secrets baked into the image
- [ ] `.dockerignore` excludes benchmark data, embed_cache, etc.

### 6. Benchmarks Dockerfile

```bash
cat benchmarks/Dockerfile
```

- [ ] All 8 tools are installed and working
- [ ] Playwright browsers are installed (`playwright install chromium`)
- [ ] Go is available for compiling colly
- [ ] Python dependencies match `requirements.txt` or `pyproject.toml`
- [ ] Colly binary is compiled fresh (not copied from host)

### 7. Docker resource usage

```bash
# Check current resource usage (if containers are running)
docker stats --no-stream 2>/dev/null || echo "No containers running"
# Check disk usage
docker system df
```

- [ ] No dangling images consuming disk
- [ ] Volume mounts don't shadow binaries (known issue: colly binary hidden by mount)

---

## What "good" looks like

- Firecrawl stack starts and stays up for a full benchmark run
- Worker memory math: `NUQ_WORKER_COUNT * max-old-space-size + overhead < mem_limit`
- No leftover NuQ jobs after restart
- Known limitations documented in reports with accurate page counts
- Dockerfiles use pinned base images, non-root users, no baked secrets
