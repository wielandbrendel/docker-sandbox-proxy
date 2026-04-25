# Tools available inside this sandbox

This file documents what tools and resources the agent has access to.
Edit it to fit your agent's purpose.

## Network

Outbound HTTP/HTTPS goes through the Docker Sandbox MITM proxy. Only
domains listed in `agent.yaml`'s `network.allow` resolve and are reachable.

## Workspace

The current directory (`workspace/`) is shared with the host. Edit files
on the host, the agent sees changes. Files the agent creates persist
on the host.
