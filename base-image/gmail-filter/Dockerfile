FROM openresty/openresty:1.25.3.2-alpine

RUN apk add --no-cache openssl bash curl

COPY entrypoint.sh /entrypoint.sh
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
RUN chmod +x /entrypoint.sh

EXPOSE 443

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
    CMD sh -c 'echo | openssl s_client -connect 127.0.0.1:443 -servername gmail.googleapis.com 2>/dev/null | grep -q "CONNECTED"'

ENTRYPOINT ["/entrypoint.sh"]
