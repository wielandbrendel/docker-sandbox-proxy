#!/bin/bash
set -e

CERT_DIR=/certs
CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"
SERVER_KEY="$CERT_DIR/server.key"
SERVER_CERT="$CERT_DIR/server.crt"
CA_BUNDLE="$CERT_DIR/ca-bundle.crt"

# Generate certs only if they don't exist (persisted via volume)
if [ ! -f "$CA_KEY" ]; then
    echo "[gmail-filter] Generating CA certificate..."
    mkdir -p "$CERT_DIR"

    # Generate CA key + cert
    openssl genrsa -out "$CA_KEY" 2048
    openssl req -new -x509 -days 3650 -key "$CA_KEY" -out "$CA_CERT" \
        -subj "/CN=Sandbox Gmail Filter CA"

    # Generate server key + CSR + cert covering all Gmail API domains
    openssl genrsa -out "$SERVER_KEY" 2048
    openssl req -new -key "$SERVER_KEY" -out "$CERT_DIR/server.csr" \
        -subj "/CN=gmail.googleapis.com"

    cat > "$CERT_DIR/ext.cnf" <<EOF
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = gmail.googleapis.com
DNS.2 = www.googleapis.com
DNS.3 = content-gmail.googleapis.com
EOF

    openssl x509 -req -days 3650 \
        -in "$CERT_DIR/server.csr" \
        -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
        -out "$SERVER_CERT" \
        -extfile "$CERT_DIR/ext.cnf" -extensions v3_req

    # Create combined CA bundle (our CA + system CAs)
    cat "$CA_CERT" /etc/ssl/certs/ca-certificates.crt > "$CA_BUNDLE"

    echo "[gmail-filter] Certificates generated."
else
    echo "[gmail-filter] Using existing certificates."
fi

echo "[gmail-filter] Starting OpenResty..."
exec /usr/local/openresty/bin/openresty -g 'daemon off;'
