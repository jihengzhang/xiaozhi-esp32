#!/bin/bash

# Configure git to use ClashCross proxy (default port: 7890)
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# Optional: Configure for SOCKS5 proxy (alternative, usually port 7891)
# git config --global http.proxy socks5://127.0.0.1:7891
# git config --global https.proxy socks5://127.0.0.1:7891

# Verify configuration
echo "=== Current git proxy settings ==="
git config --global --get http.proxy
git config --global --get https.proxy

# Test ClashCross proxy connection
echo ""
echo "=== Testing ClashCross proxy ==="
curl -x http://127.0.0.1:7890 https://www.google.com -I -m 5

# Test git connection through proxy
echo ""
echo "=== Testing git connection through ClashCross ==="
git ls-remote https://github.com/espressif/esp-idf.git HEAD
