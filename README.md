# Binance Futures Testnet Trading Bot

A lightweight Python CLI application that places Market, Limit, and Stop-Market orders on the **Binance USDT-M Futures Testnet**.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (signing, requests, logging)
│   ├── orders.py          # Order placement logic + result formatting
│   ├── validators.py      # Pure input validation (raises ValueError on failure)
│   └── logging_config.py  # Shared logger factory (file + console handlers)
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Register a Binance Futures Testnet account

1. Go to <https://testnet.binancefuture.com> and sign in with your GitHub account.
2. Navigate to **API Key** → **Generate**.
3. Copy your **API Key** and **Secret Key** — the secret is only shown once.

### 2. Clone / unzip the project

```bash
cd trading_bot
```

### 3. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set credentials

Export your testnet credentials as environment variables (safest approach):

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

Or pass them directly via `--api-key` / `--api-secret` flags (see examples below).

---

## How to Run

### Market BUY

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

**Output:**

```
====================================================
  ORDER REQUEST SUMMARY
====================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
====================================================

----------------------------------------------------
  ✓  ORDER PLACED SUCCESSFULLY
----------------------------------------------------
  Order ID     : 4611218
  Status       : FILLED
  Executed Qty : 0.001
  Avg Price    : 97423.50000
----------------------------------------------------
```

---

### Market SELL

```bash
python cli.py \
  --symbol BTCUSDT \
  --side SELL \
  --type MARKET \
  --quantity 0.001
```

---

### Limit BUY

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 0.001 \
  --price 90000
```

---

### Limit SELL

```bash
python cli.py \
  --symbol ETHUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 3500
```

---

### Stop-Market BUY (bonus order type)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type STOP_MARKET \
  --quantity 0.001 \
  --stop-price 95000
```

---

### Passing credentials inline (alternative to env vars)

```bash
python cli.py \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

---

## Logging

Logs are written to the `logs/` directory automatically (created on first run).

| File | Content |
|---|---|
| `logs/trading_bot_YYYYMMDD.log` | CLI-level events |
| `logs/binance_client_YYYYMMDD.log` | Every HTTP request, response body (truncated at 500 chars), and errors |
| `logs/orders_YYYYMMDD.log` | Order lifecycle events |

Console shows **INFO** and above. The log file captures **DEBUG** (full request/response details).

Sample log files for a market order and a limit order are included in `logs/`.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing required flag (e.g. `--price` for LIMIT) | Clear `INPUT ERROR` message, exit code 1 |
| Invalid symbol / quantity / price | Validation error printed, logged, exit code 1 |
| Missing credentials | Descriptive error with instructions, exit code 1 |
| Binance API error (e.g. insufficient balance) | `ORDER FAILED` printed with error code + message |
| Network timeout / connection refused | Exception logged, propagated to stderr |

---

## Assumptions

- The bot targets the **USDT-M Futures Testnet** only (`https://testnet.binancefuture.com`).
- Only **one-way position mode** (BOTH side) is assumed. Hedge-mode is not supported.
- Quantity precision is passed as-is; the caller must ensure it meets the symbol's `LOT_SIZE` filter. A future improvement would fetch `exchangeInfo` to auto-round.
- `timeInForce` is hardcoded to `GTC` for LIMIT orders. This could be exposed as a CLI flag if needed.
- No `.env` file loading is included — credentials are expected via environment variables or CLI flags.

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API |

Python ≥ 3.8 required (uses `from __future__ import annotations`).
