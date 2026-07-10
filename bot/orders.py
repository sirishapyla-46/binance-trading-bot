"""
Order placement logic and result formatting.

This layer sits between the CLI and the raw BinanceClient,
adding business-level logging and a uniform result structure.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger

logger = setup_logger("orders")


def _fmt(value: Optional[str], default: str = "N/A") -> str:
    """Return value if truthy and non-zero, else default."""
    if value is None:
        return default
    try:
        if Decimal(value) == 0:
            return default
    except Exception:
        pass
    return value


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal] = None,
    stop_price: Optional[Decimal] = None,
) -> dict:
    """
    Place an order via *client* and return a normalised result dict.

    Keys in the returned dict:
        success   bool
        order_id  int | None
        status    str
        executed_qty str
        avg_price    str
        raw          dict   (full API response)
        error        str | None
    """
    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    result: dict = {
        "success": False,
        "order_id": None,
        "status": "UNKNOWN",
        "executed_qty": "0",
        "avg_price": "N/A",
        "raw": {},
        "error": None,
    }

    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        result["success"] = True
        result["raw"] = raw
        result["order_id"] = raw.get("orderId")
        result["status"] = raw.get("status", "UNKNOWN")
        result["executed_qty"] = _fmt(raw.get("executedQty"))
        result["avg_price"] = _fmt(raw.get("avgPrice"))

        logger.info(
            "Order placed successfully | orderId=%s status=%s executedQty=%s avgPrice=%s",
            result["order_id"],
            result["status"],
            result["executed_qty"],
            result["avg_price"],
        )

    except BinanceAPIError as exc:
        result["error"] = str(exc)
        logger.error("Order failed (API): %s", exc)

    except Exception as exc:
        result["error"] = f"Unexpected error: {exc}"
        logger.exception("Order failed (unexpected): %s", exc)

    return result


def print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal],
    stop_price: Optional[Decimal],
) -> None:
    """Print the order request summary to stdout."""
    print("\n" + "=" * 52)
    print("  ORDER REQUEST SUMMARY")
    print("=" * 52)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")
    print("=" * 52)


def print_order_result(result: dict) -> None:
    """Print the order result to stdout."""
    print("\n" + "-" * 52)
    if result["success"]:
        print("  ✓  ORDER PLACED SUCCESSFULLY")
        print("-" * 52)
        print(f"  Order ID     : {result['order_id']}")
        print(f"  Status       : {result['status']}")
        print(f"  Executed Qty : {result['executed_qty']}")
        print(f"  Avg Price    : {result['avg_price']}")
    else:
        print("  ✗  ORDER FAILED")
        print("-" * 52)
        print(f"  Error : {result['error']}")
    print("-" * 52 + "\n")
