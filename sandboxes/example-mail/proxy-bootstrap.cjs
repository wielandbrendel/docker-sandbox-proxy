// Bootstrap proxy support for Node.js http/https modules AND undici (native fetch).
// Adapted for Docker Sandbox environment where all traffic must route through
// the MITM proxy at host.docker.internal:3128.
const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
if (proxy) {
  // --- Layer 1: classic http/https patching ---
  try {
    const http = require('http');
    const https = require('https');

    // Find https-proxy-agent from any install location
    let HttpsProxyAgent;
    const agentCandidates = [
      'https-proxy-agent',
      '/usr/local/lib/node_modules/https-proxy-agent',
      '/home/agent/.local/share/pnpm/global/5/.pnpm/https-proxy-agent@7.0.6/node_modules/https-proxy-agent',
    ];
    // Also search in openclaw's node_modules
    try {
      const oclawPath = require('child_process').execSync('which openclaw 2>/dev/null', { encoding: 'utf8' }).trim();
      if (oclawPath) {
        const fs = require('fs');
        const path = require('path');
        // Follow symlink to find the actual package
        const realPath = fs.realpathSync(oclawPath);
        const pkgDir = path.dirname(path.dirname(realPath));
        agentCandidates.push(path.join(pkgDir, 'node_modules', 'https-proxy-agent'));
      }
    } catch (_) {}

    for (const p of agentCandidates) {
      try { HttpsProxyAgent = require(p).HttpsProxyAgent; break; } catch (_) {}
    }

    if (HttpsProxyAgent) {
      const agent = new HttpsProxyAgent(proxy);
      const noProxy = (process.env.NO_PROXY || process.env.no_proxy || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
      function shouldBypass(hostname) {
        if (!hostname) return false;
        hostname = hostname.toLowerCase();
        for (const entry of noProxy) {
          if (hostname === entry) return true;
          if (entry.startsWith('.') && hostname.endsWith(entry)) return true;
        }
        return false;
      }

      function patchRequest(mod, orig) {
        return function (...args) {
          for (const arg of args) {
            if (arg && typeof arg === 'object' && !(arg instanceof URL) && typeof arg !== 'function') {
              if (!arg.agent) {
                const host = arg.hostname || arg.host || '';
                if (!shouldBypass(host.replace(/:\d+$/, ''))) {
                  arg.agent = agent;
                }
              }
              break;
            }
          }
          return orig.apply(mod, args);
        };
      }

      http.request = patchRequest(http, http.request);
      http.get = patchRequest(http, http.get);
      https.request = patchRequest(https, https.request);
      https.get = patchRequest(https, https.get);
    } else {
      console.warn('[proxy-bootstrap] Layer 1 skipped: https-proxy-agent not found');
    }
  } catch (e) {
    console.warn('[proxy-bootstrap] Layer 1 (http/https patching) failed:', e.message);
  }

  // --- Layer 2: undici global dispatcher for native fetch() ---
  try {
    let undici;
    const candidates = [
      'undici',
      '/usr/local/lib/node_modules/undici',
      '/usr/lib/node_modules/undici',
    ];
    // Search in pnpm global store
    try {
      const glob = require('fs').readdirSync('/home/agent/.local/share/pnpm/global/5/.pnpm/', { withFileTypes: true });
      for (const d of glob) {
        if (d.name.startsWith('undici@') && d.isDirectory()) {
          candidates.push(`/home/agent/.local/share/pnpm/global/5/.pnpm/${d.name}/node_modules/undici`);
        }
      }
    } catch (_) {}
    // Search in openclaw's node_modules
    try {
      const oclawPath = require('child_process').execSync('which openclaw 2>/dev/null', { encoding: 'utf8' }).trim();
      if (oclawPath) {
        const fs = require('fs');
        const path = require('path');
        const realPath = fs.realpathSync(oclawPath);
        const pkgDir = path.dirname(path.dirname(realPath));
        candidates.push(path.join(pkgDir, 'node_modules', 'undici'));
      }
    } catch (_) {}

    for (const p of candidates) {
      try { undici = require(p); break; } catch (_) {}
    }
    if (undici && undici.EnvHttpProxyAgent && undici.setGlobalDispatcher) {
      const proxyAgent = new undici.EnvHttpProxyAgent();
      undici.setGlobalDispatcher(proxyAgent);

      // --- Layer 3: Force proxy on ALL fetch calls ---
      // OpenClaw's SSRF guard creates its own Agent dispatcher for some requests,
      // bypassing the global dispatcher. In Docker Sandbox, ALL traffic MUST go
      // through the proxy. Wrap globalThis.fetch to inject the proxy dispatcher
      // when the caller provides a custom dispatcher that isn't proxy-aware.
      const origFetch = globalThis.fetch;
      globalThis.fetch = function(input, init) {
        if (init && init.dispatcher) {
          const name = init.dispatcher?.constructor?.name || '';
          if (!name.includes('Proxy') && !name.includes('EnvHttp')) {
            // Replace non-proxy dispatcher with our proxy agent
            init = { ...init, dispatcher: proxyAgent };
          }
        }
        return origFetch.call(this, input, init);
      };
    } else {
      console.warn('[proxy-bootstrap] Layer 2 skipped: undici not found or missing exports');
    }
  } catch (e) {
    console.warn('[proxy-bootstrap] Layer 2 (undici fetch proxy) failed:', e.message);
  }
}
