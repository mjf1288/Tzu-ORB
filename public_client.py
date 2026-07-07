# public_client.py

import requests
from typing import Any, Sequence


class PublicClient:
    """
    Thin wrapper around the Public Trading API.

    You should fill in the actual endpoint paths from Public's docs:
    - Quotes / intraday bars
    - Option chain with greeks
    - Preflight multi-leg
    - Place multi-leg order
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # --- Market data ---

    def get_intraday_bars(
        self,
        symbol: str,
        start_iso: str,
        end_iso: str,
        interval: str = "1m",
    ) -> list[dict]:
        """
        Returns a list of OHLCV bars for the symbol between start_iso and end_iso.

        You need to map this to Public's market data endpoint or your own feed.
        Return format per bar:
        {
          "time": "...",
          "open": float,
          "high": float,
          "low": float,
          "close": float,
          "volume": int
        }
        """
        # TODO: implement using Public's data endpoints.
        # For now, return empty list so the engine fails gracefully.
        return []

    def get_recent_opening_volumes(self, symbol: str, days: int = 20) -> list[float]:
        """
        Returns a list of opening range volumes for the last N sessions.
        You can compute this from stored tape or Public intraday data.
        """
        # TODO: implement real volume history.
        return []

    def get_option_chain_with_greeks(self, underlying: str) -> Any:
        """
        Call Public's option chain/greeks endpoint for the given underlying.
        Use this later for routing/proposals. [web:13][web:24][web:248]
        """
        # TODO: implement chain+greeks call.
        return {}

    # --- Orders ---

    def preflight_multileg(self, payload: dict) -> dict:
        """
        Preflight a multi-leg strategy via Public. [web:20][web:23]
        """
        url = f"{self.base_url}/order-placement/preflight-multi-leg"
        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    def place_multileg_order(self, payload: dict) -> dict:
        """
        Place a multi-leg options order via Public. [web:22][web:249]
        """
        url = f"{self.base_url}/order-placement/place-multileg-order"
        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()
