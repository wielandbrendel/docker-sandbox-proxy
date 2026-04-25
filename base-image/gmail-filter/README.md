# gmail-filter base image (opt-in)

OpenResty + Lua MITM proxy for operation-level Gmail API filtering.

**This image is only used when an agent has `gmail_filter.enabled: true` in its agent.yaml.** See [docs/gmail-filter.md](../../docs/gmail-filter.md) for setup details.

## What it filters

The Lua allowlist permits read operations and draft management; everything
else returns 403. See `nginx.conf` for the exact allowlist.

Allowed (examples):
- GET requests on `gmail.googleapis.com`
- POST `/gmail/v1/users/*/drafts` (create draft)
- POST `/gmail/v1/users/*/messages/*/modify` (modify labels, used for archiving)
- PUT/DELETE on draft IDs

Blocked (examples):
- Sending email
- Permanent deletion of messages/threads
- Batch operations
- X-HTTP-Method-Override header smuggling
