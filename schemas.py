from pydantic import BaseModel, Field
from typing import Optional, List


# ---------- Request ----------

class LoginRequest(BaseModel):
    login: int = Field(..., description="MT5 account number")
    password: str = Field(..., description="MT5 account password")
    server: str = Field(..., description="MT5 broker server name")


# ---------- Sub-models ----------

class AccountInfo(BaseModel):
    login: int
    name: str
    server: str
    currency: str
    leverage: int
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: Optional[float]
    margin_call_level: float
    margin_stopout_level: float
    trade_allowed: bool
    trade_expert: bool
    account_type: str


class Position(BaseModel):
    ticket: int
    symbol: str
    type: str          # "buy" or "sell"
    volume: float
    open_price: float
    open_time: str
    sl: float
    tp: float
    current_price: float
    swap: float
    profit: float
    comment: str
    magic: int


class PendingOrder(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: float
    open_price: float
    open_time: str
    sl: float
    tp: float
    comment: str
    magic: int


class Deal(BaseModel):
    ticket: int
    order: int
    symbol: str
    type: str
    entry: str          # "in", "out", "in/out"
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    comment: str
    time: str


class HistoricalOrder(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume_initial: float
    volume_current: float
    open_price: float
    open_time: str
    close_time: Optional[str]
    sl: float
    tp: float
    state: str
    comment: str
    magic: int


class SymbolTick(BaseModel):
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: str


# ---------- Top-level response ----------

class AccountDetailsResponse(BaseModel):
    account_info: AccountInfo
    open_positions: List[Position]
    pending_orders: List[PendingOrder]
    deals_history: List[Deal]
    orders_history: List[HistoricalOrder]
    symbols_trading: List[str]


class ErrorResponse(BaseModel):
    error: str
    code: Optional[int] = None
