"""
Binance Futures Testnet REST API client.

Handles authentication (HMAC-SHA256 signing), request execution,
logging of every request/response, and consistent error surfacing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

BASE_URL = "https://testnet.binancefuture.com"

logger = setup_logger("binance_client")


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin, signed wrapper around the Binance USDT-M Futures REST API.

    Args:
        api_key:    Testnet API key.
        api_secret: Testnet API secret.
        base_url:   Base URL (defaults to testnet).
        timeout:    HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = BASE_URL,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised. Base URL: %s", self._base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append a HMAC-SHA256 signature to *params* and return it."""
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        sig = hmac.new(self._api_secret, query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        return params

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request, log it, and return the parsed JSON.

        Raises:
            BinanceAPIError: on non-2xx API responses.
            requests.RequestException: on network-level errors.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self._base_url}{path}"
        logger.debug("REQUEST  %s %s | params=%s", method.upper(), url, params)

        try:
            resp = self._session.request(
                method,
                url,
                params=params if method.upper() == "GET" else None,
                data=params if method.upper() != "GET" else None,
                timeout=self._timeout,
            )
        except requests.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request timed out after %ss", self._timeout)
            raise

        logger.debug(
            "RESPONSE %s %s | status=%s | body=%s",
            method.upper(),
            url,
            resp.status_code,
            resp.text[:500],  # truncate very long bodies in log
        )

        data = resp.json()

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            err = BinanceAPIError(data["code"], data.get("msg", "Unknown error"))
            logger.error("API error: %s", err)
            raise err

        if not resp.ok:
            logger.error(
                "HTTP error %s: %s", resp.status_code, resp.text[:200]
            )
            resp.raise_for_status()

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange metadata (symbols, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        """Fetch account balances and positions."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a new futures order.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'.
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET', 'LIMIT', or 'STOP_MARKET'.
            quantity:      Order quantity.
            price:         Limit price (LIMIT orders only).
            stop_price:    Trigger price (STOP_MARKET orders only).
            time_in_force: 'GTC', 'IOC', or 'FOK' (LIMIT only).

        Returns:
            Parsed JSON response from the API.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["stopPrice"] = str(stop_price)

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stopPrice=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
            stop_price,
        )
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a single order by ID."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params=params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)
