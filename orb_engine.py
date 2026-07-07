# orb_engine.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Literal, Optional
from datetime import datetime, time, timedelta, timezone

from public_client import PublicClient


Direction = Literal["bull", "bear", "neutral"]


@dataclass
class Signal:
    symbol: str
    score: float
    direction: Direction


@dataclass
class EngineState:
    signals: List[Signal]
    proposals: int
    staged_orders: int
    routing_mode: str  # "paper" or "live"


class ORBEngine:
    """
    Opening Range Breakout engine that uses market data (via PublicClient)
    to compute per-symbol ORB scores and directions.
    """

    def __init__(
        self,
        public_client: PublicClient,
        universe: list[str],
        orb_minutes: int = 30,
        routing_mode: str = "paper",
    ):
        self.public = public_client
        self.universe = universe
        self.orb_minutes = orb_minutes
        self.routing_mode = routing_mode

    # --- Public-facing API ---

    def compute_state(self) -> EngineState:
        signals: list[Signal] = []

        for symbol in self.universe:
            sig = self._compute_symbol_signal(symbol)
            if sig is not None:
                signals.append(sig)

        # Sort by score descending
        signals.sort(key=lambda s: s.score, reverse=True)

        # Simple proposal logic: count signals above threshold
        proposals = sum(1 for s in signals if s.score >= 70.0)
        staged_orders = 0  # later: count multi-leg structures you've actually staged

        return EngineState(
            signals=signals,
            proposals=proposals,
            staged_orders=staged_orders,
            routing_mode=self.routing_mode,
        )

    def to_dict(self) -> dict:
        state = self.compute_state()
        d = asdict(state)
        d["signals"] = [asdict(sig) for sig in state.signals]
        return d

    # --- ORB logic ---

    def _market_times_today(self) -> tuple[datetime, datetime]:
        """
        Returns today's session start and end in ET as ISO datetimes.
        Adjust timezone handling as needed.
        """
        # Assuming server running in ET; if not, convert appropriately.
        now = datetime.now(timezone.utc).astimezone()
        session_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
        session_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return session_start, session_end

    def _compute_symbol_signal(self, symbol: str) -> Optional[Signal]:
        session_start, _ = self._market_times_today()
        orb_end = session_start + timedelta(minutes=self.orb_minutes)
        post_end = orb_end + timedelta(minutes=30)  # evaluation window

        # Convert to ISO strings for Public client
        start_iso = session_start.isoformat()
        orb_end_iso = orb_end.isoformat()
        post_end_iso = post_end.isoformat()

        # 1. Load ORB bars
        bars = self.public.get_intraday_bars(
            symbol=symbol,
            start_iso=start_iso,
            end_iso=orb_end_iso,
            interval="1m",
        )
        if not bars:
            return None

        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]
        vols = [b["volume"] for b in bars]

        H_orb = max(highs)
        L_orb = min(lows)
        R = H_orb - L_orb
        M = (H_orb + L_orb) / 2.0
        V_orb = sum(vols)

        P_open = bars[0]["open"]

        # 2. Baseline opening volume (simple avg)
        recent_vols = self.public.get_recent_opening_volumes(symbol, days=20)
        V_avg = sum(recent_vols) / len(recent_vols) if recent_vols else None

        # 3. Hard filters: range & volume
        min_R = 0.002 * P_open   # 0.2% of price
        max_R = 0.015 * P_open   # 1.5% of price

        if R < min_R or R > max_R:
            return Signal(symbol=symbol, score=0.0, direction="neutral")

        if V_avg is not None and V_orb < 1.2 * V_avg:
            return Signal(symbol=symbol, score=0.0, direction="neutral")

        # 4. Evaluate breakout in post-ORB window
        post_bars = self.public.get_intraday_bars(
            symbol=symbol,
            start_iso=orb_end_iso,
            end_iso=post_end_iso,
            interval="1m",
        )
        if not post_bars:
            return Signal(symbol=symbol, score=0.0, direction="neutral")

        P_last = post_bars[-1]["close"]

        # Determine direction
        if P_last > H_orb:
            direction: Direction = "bull"
            d = (P_last - H_orb) / R
        elif P_last < L_orb:
            direction = "bear"
            d = (L_orb - P_last) / R
        else:
            direction = "neutral"
            d = 0.0

        # Breakout conviction
        q_break = min(max(d, 0.0), 1.0)

        # Range quality
        R_star = 0.004 * P_open   # ideal ~0.4% range
        q_range = 1.0 - abs(R - R_star) / R_star
        q_range = min(max(q_range, 0.0), 1.0)

        # Volume quality
        if V_avg is not None:
            q_vol = min(V_orb / (1.5 * V_avg), 1.0)
        else:
            q_vol = 0.5  # unknown baseline; neutral

        # Optional retest (stubbed as 0; you can implement later)
        q_retest = 0.0

        # Weighted score
        w_range, w_vol, w_break, w_retest = 0.25, 0.25, 0.4, 0.1
        raw = w_range * q_range + w_vol * q_vol + w_break * q_break + w_retest * q_retest

        score = 100.0 * max(0.0, min(raw, 1.0))

        if direction == "neutral":
            score = 0.0

        return Signal(symbol=symbol, score=score, direction=direction)
