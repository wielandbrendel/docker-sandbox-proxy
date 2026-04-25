# Gmail Filter

The Gmail filter is an optional sidecar that intercepts Gmail API traffic at
the operation level. The agent can read mail, create drafts, and archive, but
cannot send email or permanently delete anything.

Enable it with `gmail_filter.enabled: true` in `agent.yaml`.

## Architecture

```
agent process
    │  HTTPS to gmail.googleapis.com
    ▼
Docker Sandbox HTTPS proxy
    │  proxy rewrites host to gmail-filter (localhost:http_port)
    ▼
gmail-filter container (OpenResty + Lua)
    │  CA terminates TLS, inspects request
    │  allowed → forward to real Gmail API
    │  blocked → return 403
    ▼
gmail.googleapis.com (real API)
```

The filter uses HTTPS MITM: it presents a self-signed certificate (signed by
a locally-generated CA) to the agent, inspects the plaintext request, then
re-encrypts to the real Gmail API. The agent trusts the filter's CA via:

- `NODE_EXTRA_CA_CERTS`
- `REQUESTS_CA_BUNDLE`
- `SSL_CERT_FILE`
- `CURL_CA_BUNDLE`

These are injected into the agent environment by `start.py` at boot time.

## Allowed and blocked operations

### `gmail.googleapis.com`

| Method | Path pattern | Result |
|--------|-------------|--------|
| `GET` | any | Allowed (all reads) |
| `POST` | `/gmail/v1/users/*/drafts` | Allowed (create draft) |
| `PUT` | `/gmail/v1/users/*/drafts/*` | Allowed (update draft) |
| `DELETE` | `/gmail/v1/users/*/drafts/*` | Allowed (delete draft) |
| `POST` | `/gmail/v1/users/*/messages/*/modify` | Allowed (labels — used for archiving) |
| `POST` | `/gmail/v1/users/*/messages/send` | **Blocked (403)** |
| `POST` | `/gmail/v1/users/*/drafts/send` | **Blocked (403)** |
| `DELETE` | `/gmail/v1/users/*/messages/*` | **Blocked (403)** |
| `DELETE` | `/gmail/v1/users/*/threads/*` | **Blocked (403)** |
| `POST` | `*/batchDelete` | **Blocked (403)** |
| `POST` | `*/batchModify` (not modify) | **Blocked (403)** |
| `POST` | `/gmail/v1/users/*/messages/import` | **Blocked (403)** |
| any | `*/settings/*` | **Blocked (403)** |
| any | `*/batch` | **Blocked (403)** |

### `content-gmail.googleapis.com` (upload endpoint)

| Method | Path | Result |
|--------|------|--------|
| `GET` | any | Allowed |
| `POST` | `/gmail/v1/users/*/drafts` | Allowed (create draft with attachment) |
| `PUT` | `/gmail/v1/users/*/drafts/*` | Allowed (update draft with attachment) |
| anything else | — | **Blocked (403)** |

### `www.googleapis.com`

All `/gmail/v1/` paths are blocked. Other Google APIs pass through.

## Anti-bypass protections

The Lua code normalises every URI before matching:

- **Percent-decoding**: `%2F` → `/` (blocks `/messages%2Fsend`)
- **Double-encoding rejection**: `%252F` returns 400
- **Null-byte rejection**: any `%00` returns 400
- **Path normalization**: collapses `//`, resolves `.` and `..` segments
- **`X-HTTP-Method-Override` stripping**: prevents method override tricks

## Extending the filter

Edit `base-image/gmail-filter/nginx.conf`. The Lua allowlist is in the
`content_by_lua_block` sections. After editing, rebuild and restart:

```bash
docker build -t gmail-filter:latest base-image/gmail-filter/
sandbox restart my-agent
```

## Debugging

Filter logs inside the `gmail-filter` container:

```bash
docker logs gmail-filter-my-agent
```

For detailed Nginx error logs:

```bash
docker exec gmail-filter-my-agent cat /var/log/nginx/error.log
```

A 403 response from the filter looks like:

```
2026/04/01 12:00:00 [notice] 42#0: *1 lua: BLOCKED POST /gmail/v1/users/me/messages/send
```

## Certificate regeneration

Certificates are generated once by `start.py` and stored in
`sandboxes/my-agent/gmail-filter-certs/`. They do not expire for 10 years.
If you need to regenerate them (e.g. after a `sandbox destroy`):

```bash
sandbox start my-agent   # automatically regenerates if certs dir is empty
```
