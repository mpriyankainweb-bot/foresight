# Foresight CLI

Install locally with:

```bash
pip install -e cli/
```

Usage:

```bash
foresight check \
  --service payments-gateway \
  --title "Lower retry timeout from 30s to 8s" \
  --diff ./change.diff \
  --config-changes "GATEWAY_RETRY_TIMEOUT_MS=8000"
```

Exit codes:
- `0`: SHIP (Safe to ship)
- `1`: CANARY (Ship only with canary verification)
- `2`: HOLD (Blocked due to memory-recalled incident risks)
