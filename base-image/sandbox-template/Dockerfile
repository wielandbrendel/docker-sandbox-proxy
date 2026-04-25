# Sandbox template: Node 22 Alpine with OpenClaw, pnpm, gogcli pre-installed.
# Used as: docker sandbox create --template sandbox-openclaw:latest shell /workspace
#
# Build: docker build -t sandbox-openclaw:latest base-image/sandbox-template/
# Use:   docker sandbox create --template sandbox-openclaw:latest --name my-agent shell ~/my-workspace

FROM node:22-alpine

ARG OPENCLAW_VERSION=2026.4.11
ARG GOGCLI_VERSION=0.11.0

# System packages
RUN apk add --no-cache bash curl git jq ca-certificates sudo shadow procps

# pnpm
RUN npm install -g pnpm

# Create docker group and agent user (matches Docker Sandbox convention)
# node:22-alpine already has uid 1000 as 'node', rename it
RUN addgroup -S docker 2>/dev/null || true && \
    deluser node 2>/dev/null; \
    adduser -D -s /bin/bash -u 1000 agent && \
    addgroup agent docker 2>/dev/null || true && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/agent && chown agent:agent /home/agent

# Install OpenClaw as agent user
USER agent
ENV PNPM_HOME=/home/agent/.local/share/pnpm
ENV PATH=/usr/local/bin:${PNPM_HOME}:$PATH
RUN pnpm install -g openclaw@${OPENCLAW_VERSION} https-proxy-agent undici

# Install gogcli
USER root
RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
      aarch64|arm64) GOARCH=arm64 ;; \
      x86_64|amd64)  GOARCH=amd64 ;; \
    esac && \
    curl -sL "https://github.com/steipete/gogcli/releases/download/v${GOGCLI_VERSION}/gogcli_${GOGCLI_VERSION}_linux_${GOARCH}.tar.gz" \
      | tar xz -C /usr/local/bin gog

# Entrypoint: auto-starts OpenClaw from workspace init script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER root
ENTRYPOINT ["/entrypoint.sh"]
