"""
mt5_client.py
Handles all MetaTrader 5 interactions in a thread-safe way.
Each call performs its own initialize() / shutdown() cycle so that
multiple threads can work concurrently without sharing MT5 state.
"""

import threading
import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from config import settings

# One lock per thread ensures that the global MT5 handle is not
# shared across threads simultaneously.
_thread_local = threading.local()


# ------------------------------------------------------------------ #
#  Internal helpers
# ------------------------------------------------------------------ #

def _position_type_str(type_int: int) -> str:
    return {0: "buy", 1: "sell"}.get(type_int, str(type_int))


def _order_type_str(type_int: int) -> str:
    mapping = {
        0: "buy",
        1: "sell",
        2: "buy_limit",
        3: "sell_limit",
        4: "buy_stop",
        5: "sell_stop",
        6: "buy_stop_limit",
        7: "sell_stop_limit",
        8: "close_by",
    }
    return mapping.get(type_int, str(type_int))


def _deal_type_str(type_int: int) -> str:
    mapping = {
        0: "buy",
        1: "sell",
        2: "balance",
        3: "credit",
        4: "charge",
        5: "correction",
        6: "bonus",
        7: "commission",
        8: "commission_daily",
        9: "commission_monthly",
        10: "commission_agent_daily",
        11: "commission_agent_monthly",
        12: "interest",
        13: "buy_canceled",
        14: "sell_canceled",
        15: "dividend",
        16: "dividend_franked",
        17: "tax",
    }
    return mapping.get(type_int, str(type_int))


def _deal_entry_str(entry_int: int) -> str:
    return {0: "in", 1: "out", 2: "in/out", 3: "out_by"}.get(entry_int, str(entry_int))


def _order_state_str(state_int: int) -> str:
    mapping = {
        0: "started",
        1: "placed",
        2: "canceled",
        3: "partial",
        4: "filled",
        5: "rejected",
        6: "expired",
        7: "request_add",
        8: "request_modify",
        9: "request_cancel",
    }
    return mapping.get(state_int, str(state_int))


def _ts(epoch: int) -> str:
    """Convert a Unix timestamp (seconds) to an ISO-8601 string."""
    if not epoch:
        return ""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _account_type_str(t: int) -> str:
    return {0: "real", 1: "demo", 2: "contest"}.get(t, str(t))


# ------------------------------------------------------------------ #
#  Core fetch function
# ------------------------------------------------------------------ #

def fetch_account_details(login: int, password: str, server: str) -> Dict[str, Any]:
    """
    Initialise an MT5 connection for the given credentials, pull all
    available account data, then shut down.  Returns a plain dict that
    is later serialised to JSON by FastAPI.

    Raises RuntimeError on any MT5 error so the caller can map it to
    an appropriate HTTP response.
    """

    # --- initialise MT5 ---
    ok = mt5.initialize(login=login, password=password, server=server,
                        timeout=settings.mt5_timeout * 1000)
    if not ok:
        err = mt5.last_error()
        raise RuntimeError(f"MT5 initialise failed: {err[1]} (code {err[0]})")

    try:
        # ---- account info ------------------------------------------------
        ai = mt5.account_info()
        if ai is None:
            err = mt5.last_error()
            raise RuntimeError(f"account_info() failed: {err[1]} (code {err[0]})")

        account_info = {
            "login": ai.login,
            "name": ai.name,
            "server": ai.server,
            "currency": ai.currency,
            "leverage": ai.leverage,
            "balance": ai.balance,
            "credit": ai.credit,
            "profit": ai.profit,
            "equity": ai.equity,
            "margin": ai.margin,
            "margin_free": ai.margin_free,
            "margin_level": ai.margin_level if ai.margin_level else None,
            "margin_call_level": ai.margin_so_call,
            "margin_stopout_level": ai.margin_so_so,
            "trade_allowed": bool(ai.trade_allowed),
            "trade_expert": bool(ai.trade_expert),
            "account_type": _account_type_str(ai.trade_mode),
        }

        # ---- open positions ----------------------------------------------
        raw_positions = mt5.positions_get()
        open_positions = []
        if raw_positions:
            for p in raw_positions:
                open_positions.append({
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": _position_type_str(p.type),
                    "volume": p.volume,
                    "open_price": p.price_open,
                    "open_time": _ts(p.time),
                    "sl": p.sl,
                    "tp": p.tp,
                    "current_price": p.price_current,
                    "swap": p.swap,
                    "profit": p.profit,
                    "comment": p.comment,
                    "magic": p.magic,
                })

        # ---- pending orders ----------------------------------------------
        raw_orders = mt5.orders_get()
        pending_orders = []
        if raw_orders:
            for o in raw_orders:
                pending_orders.append({
                    "ticket": o.ticket,
                    "symbol": o.symbol,
                    "type": _order_type_str(o.type),
                    "volume": o.volume_initial,
                    "open_price": o.price_open,
                    "open_time": _ts(o.time_setup),
                    "sl": o.sl,
                    "tp": o.tp,
                    "comment": o.comment,
                    "magic": o.magic,
                })

        # ---- deals history -----------------------------------------------
        date_from = datetime.now(tz=timezone.utc) - timedelta(days=settings.history_days)
        date_to = datetime.now(tz=timezone.utc) + timedelta(days=1)

        raw_deals = mt5.history_deals_get(date_from, date_to)
        deals_history = []
        if raw_deals:
            for d in raw_deals:
                deals_history.append({
                    "ticket": d.ticket,
                    "order": d.order,
                    "symbol": d.symbol,
                    "type": _deal_type_str(d.type),
                    "entry": _deal_entry_str(d.entry),
                    "volume": d.volume,
                    "price": d.price,
                    "commission": d.commission,
                    "swap": d.swap,
                    "profit": d.profit,
                    "fee": d.fee,
                    "comment": d.comment,
                    "time": _ts(d.time),
                })

        # ---- historical orders -------------------------------------------
        raw_hist_orders = mt5.history_orders_get(date_from, date_to)
        orders_history = []
        if raw_hist_orders:
            for o in raw_hist_orders:
                orders_history.append({
                    "ticket": o.ticket,
                    "symbol": o.symbol,
                    "type": _order_type_str(o.type),
                    "volume_initial": o.volume_initial,
                    "volume_current": o.volume_current,
                    "open_price": o.price_open,
                    "open_time": _ts(o.time_setup),
                    "close_time": _ts(o.time_done) if o.time_done else None,
                    "sl": o.sl,
                    "tp": o.tp,
                    "state": _order_state_str(o.state),
                    "comment": o.comment,
                    "magic": o.magic,
                })

        # ---- symbols the account has traded ------------------------------
        traded_symbols = list({p["symbol"] for p in open_positions} |
                              {d["symbol"] for d in deals_history if d["symbol"]})

        return {
            "account_info": account_info,
            "open_positions": open_positions,
            "pending_orders": pending_orders,
            "deals_history": deals_history,
            "orders_history": orders_history,
            "symbols_trading": sorted(traded_symbols),
        }

    finally:
        mt5.shutdown()
