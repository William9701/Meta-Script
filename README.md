# MetaTrader 5 Account API

A lightweight REST API built with **FastAPI** that lets you fetch complete MetaTrader 5 (MT5) account data — balance, equity, open positions, pending orders, deal history, and more — via a single HTTP POST request.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Starting the Server](#starting-the-server)
- [API Endpoints](#api-endpoints)
- [Example Request & Response](#example-request--response)
- [Interactive Docs (Swagger UI)](#interactive-docs-swagger-ui)
- [Load Testing](#load-testing)
- [Project Structure](#project-structure)

---

## Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows only (MetaTrader5 Python package is Windows-exclusive) |
| **Python** | 3.8 or higher |
| **MetaTrader 5** | MT5 terminal must be installed on the same machine |

---

## Installation

**1. Clone or download this repository**

```bash
git clone git@github.com:William9701/Meta-Script.git
cd Meta-Script
```

**2. Create and activate a virtual environment** (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```


---

## Starting the Server

**Option 1 — Recommended (uvicorn CLI):**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

**Option 2 — Run directly with Python:**

```bash
python main.py
```

> **Note:** Always use `--workers 1`. Concurrency is handled internally with a `ThreadPoolExecutor`, so multiple uvicorn workers are not needed and may cause issues with the MT5 terminal.

The server will start and be accessible at `http://localhost:8000`.

---

## API Endpoints

### `GET /health`

Simple liveness check. Use this to confirm the server is running.

```
GET http://localhost:8000/health
```

**Response:**
```json
{ "status": "ok" }
```

---

### `POST /account/details`

Logs in to an MT5 account and returns all available account data.

**Request body (JSON):**

| Field | Type | Description |
|---|---|---|
| `login` | integer | Your MT5 account number |
| `password` | string | Your MT5 account password |
| `server` | string | Your broker's MT5 server name (e.g. `"MetaQuotes-Demo"`) |

**Response fields:**

| Field | Description |
|---|---|
| `account_info` | Balance, equity, margin, leverage, account type, etc. |
| `open_positions` | All currently open trades |
| `pending_orders` | All pending/limit/stop orders |
| `deals_history` | Closed deals from the last N days (set by `HISTORY_DAYS`) |
| `orders_history` | Historical orders from the last N days |
| `symbols_trading` | Sorted list of symbols this account has traded |

**Error responses:**

| Status | Meaning |
|---|---|
| `400` | Bad credentials or MT5 connection error |
| `500` | Unexpected internal server error |

---

## Example Request & Response

**Using `curl`:**

```bash
curl -X POST http://localhost:8000/account/details \
  -H "Content-Type: application/json" \
  -d "{\"login\": 12345678, \"password\": \"yourpassword\", \"server\": \"YourBroker-Server\"}"
```

**Using Python (`requests` library):**

```python
import requests

response = requests.post(
    "http://localhost:8000/account/details",
    json={
        "login": 12345678,
        "password": "yourpassword",
        "server": "YourBroker-Server"
    }
)

data = response.json()
print(data["account_info"]["balance"])
print(data["open_positions"])
```

**Example response (abbreviated):**

```json
{
  "account_info": {
    "login": 12345678,
    "name": "John Doe",
    "server": "YourBroker-Server",
    "currency": "USD",
    "leverage": 100,
    "balance": 10000.00,
    "equity": 10250.00,
    "margin": 500.00,
    "margin_free": 9750.00,
    "margin_level": 2050.0,
    "account_type": "demo",
    "trade_allowed": true,
    "trade_expert": true
  },
  "open_positions": [
    {
      "ticket": 123456,
      "symbol": "EURUSD",
      "type": "buy",
      "volume": 0.1,
      "open_price": 1.08500,
      "current_price": 1.09000,
      "profit": 50.00,
      "sl": 1.08000,
      "tp": 1.10000
    }
  ],
  "pending_orders": [],
  "deals_history": [...],
  "orders_history": [...],
  "symbols_trading": ["EURUSD", "GBPUSD"]
}
```

---

## Interactive Docs (Swagger UI)

FastAPI generates interactive API documentation automatically. Once the server is running, open your browser and go to:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

You can test the API directly from the browser without needing `curl` or Postman.

---

## Load Testing

A load test script is included to simulate 20 concurrent users hitting the API simultaneously.

**Before running**, edit [load_test.py](load_test.py) and replace the placeholder credentials with your own:

```python
PAYLOAD = json.dumps({
    "login": YOUR_LOGIN,
    "password": "YOUR_PASSWORD",
    "server": "YOUR_SERVER"
}).encode("utf-8")
```

**Run the load test** (server must be running first):

```bash
python load_test.py
```

It will print a table showing each thread's response time, HTTP status, balance, equity, open positions, and deal count — plus averages at the end.

---

## Project Structure

```
Meta-Script/
├── main.py            # FastAPI app, routes, and entry point
├── mt5_client.py      # MT5 connection logic and data fetching
├── schemas.py         # Pydantic request/response models
├── config.py          # Settings (env vars / .env file)
├── load_test.py       # Concurrent load testing script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## How It Works

1. You send a POST request with your MT5 login credentials.
2. The API spins up a thread from its pool (up to `MAX_WORKERS` at once).
3. Each thread initializes its own MT5 connection, fetches all account data, then shuts down the connection cleanly.
4. The data is returned as a structured JSON response.

This design allows multiple requests to be handled concurrently without MT5 state being shared or corrupted between threads.
