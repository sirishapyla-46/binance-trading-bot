"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500

# Stop-Market BUY (bonus)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 90000

Credentials are read from environment variables:
    BINANCE_API_KEY
    BINANCE_API_SECRET

Or you can pass them as flags (--api-key / --api-secret).
"""

from __future__ import annotations

import argparse
import os
import sys

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order, print_order_result, print_order_summary
from bot.validators import validate_order_params

logger = setup_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Credentials (optional; fall back to env vars)
    creds = parser.add_argument_group("credentials (env vars preferred)")
    creds.add_argument(
        "--api-key",
        default=None,
        help="Binance Testnet API key (or set BINANCE_API_KEY env var).",
    )
    creds.add_argument(
        "--api-secret",
        default=None,
        help="Binance Testnet API secret (or set BINANCE_API_SECRET env var).",
    )

    # Order params
    order = parser.add_argument_group("order parameters")
    order.add_argument(
        "--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT."
    )
    order.add_argument(
        "--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL."
    )
    order.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "market", "limit", "stop_market"],
        help="Order type: MARKET, LIMIT, or STOP_MARKET.",
    )
    order.add_argument(
        "--quantity", required=True,
        help="Order quantity (base asset)."
    )
    order.add_argument(
        "--price", default=None,
        help="Limit price (required for LIMIT orders)."
    )
    order.add_argument(
        "--stop-price", default=None, dest="stop_price",
        help="Stop trigger price (required for STOP_MARKET orders)."
    )

    # Misc
    parser.add_argument(
        "--base-url",
        default="https://testnet.binancefuture.com",
        help="Binance Futures base URL (default: testnet).",
    )

    return parser


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """Return (api_key, api_secret) from args or env vars."""
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    if not api_key:
        logger.error("API key not provided. Set --api-key or BINANCE_API_KEY.")
        print("\n  ERROR: API key is required.\n"
              "  Set the BINANCE_API_KEY environment variable or pass --api-key.\n")
        sys.exit(1)

    if not api_secret:
        logger.error("API secret not provided. Set --api-secret or BINANCE_API_SECRET.")
        print("\n  ERROR: API secret is required.\n"
              "  Set the BINANCE_API_SECRET environment variable or pass --api-secret.\n")
        sys.exit(1)

    return api_key, api_secret


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger.info(
        "CLI invoked | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        args.symbol, args.side, args.order_type,
        args.quantity, args.price, args.stop_price,
    )

    # 1. Validate inputs
    try:
        params = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n  INPUT ERROR: {exc}\n")
        sys.exit(1)

    # 2. Print summary
    print_order_summary(
        symbol=params["symbol"],
        side=params["side"],
        order_type=params["order_type"],
        quantity=params["quantity"],
        price=params["price"],
        stop_price=params["stop_price"],
    )

    # 3. Resolve credentials & build client
    api_key, api_secret = resolve_credentials(args)
    client = BinanceClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url=args.base_url,
    )

    # 4. Place order
    result = place_order(
        client=client,
        symbol=params["symbol"],
        side=params["side"],
        order_type=params["order_type"],
        quantity=params["quantity"],
        price=params["price"],
        stop_price=params["stop_price"],
    )

    # 5. Print result
    print_order_result(result)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
