FROM python:3.12-slim

RUN groupadd -r markcrawl && useradd -r -g markcrawl markcrawl

WORKDIR /app

# Install the package
COPY . .
RUN pip install --no-cache-dir ".[mcp]"

USER markcrawl

# MCP servers communicate over stdio
ENTRYPOINT ["python", "-m", "markcrawl.mcp_server"]
