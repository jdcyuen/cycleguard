# src/engine/market_phase_detector.p



import pandas as pd
import yfinance as yf

from config.config_manager import get_config
from engine.regime.signals.trend import TrendSignal
from engine.regime.signals.breadth import BreadthSignal
from engine.regime.signals.volatility import VolatilitySignal


class MarketPhaseDetector:
    """
    Evaluates market conditions against the 4-input signal stack
    to determine the current portfolio allocation regime.
    """

    def __init__(self, config=None):
        self.config = config if config else get_config()
        self.regime_config = self.config.get("regime_system", {})
        self.signals = self.regime_config.get("signals", {})

        

    def _fetch_daily_closes(self, tickers: list, period="1y") -> pd.DataFrame:
        """Batch download daily closing prices for a list of tickers to minimize network overhead."""
        if not tickers:
            return pd.DataFrame()

        df = yf.download(tickers, period=period, progress=False, auto_adjust=False)

        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            return df["Close"]
        else:
            # Single ticker case
            res = pd.DataFrame(df["Close"])
            res.columns = [tickers[0]]
            return res

    def get_trend_signal(self, current: float, dma50: float, dma200: float) -> str:
        if current > dma200:
            return "Bullish"
        elif min(dma50, dma200) <= current <= max(dma50, dma200):
            return "Neutral"
        else:
            return "Bearish"

    def get_breadth_signal(self, pct_above_50: float) -> str:
        strong_threshold = (
            self.signals.get("breadth", {}).get("thresholds", {}).get("strong", 65)
        )
        weak_threshold = (
            self.signals.get("breadth", {}).get("thresholds", {}).get("weak", 50)
        )

        if pct_above_50 > strong_threshold:
            return "Strong"
        elif pct_above_50 < weak_threshold:
            return "Weak"
        else:
            return "Improving"

    def get_vix_signal(self, current_vix: float) -> str:
        calm_threshold = (
            self.signals.get("volatility", {}).get("thresholds", {}).get("calm", 18)
        )
        risk_off_threshold = (
            self.signals.get("volatility", {}).get("thresholds", {}).get("risk_off", 25)
        )

        if current_vix < calm_threshold:
            return "Calm"
        elif current_vix > risk_off_threshold:
            return "Risk-off"
        else:
            return "Neutral"

    def get_leadership_signal(
        self, qqq_current: float, qqq_50: float, smh_current: float, smh_50: float
    ) -> str:
        # Strong if BOTH are above 50DMA, Weak if BOTH are below. Mixed otherwise.
        qqq_strong = qqq_current > qqq_50
        smh_strong = smh_current > smh_50

        if qqq_strong and smh_strong:
            return "Strong"
        elif not qqq_strong and not smh_strong:
            return "Weak"
        else:
            return "Mixed"

    def get_credit_signal(
        self, jnk_price: float, shy_price: float, jnk_50: float, shy_50: float
    ) -> str:
        current_ratio = jnk_price / shy_price if shy_price > 0 else 0
        ratio_50 = jnk_50 / shy_50 if shy_50 > 0 else 0
        if current_ratio > ratio_50:
            return "Healthy"
        else:
            return "Stressed"

    def run(self) -> dict:
        """
        Executes the 5-input signal stack and aggregates a score to determine the Regime.
        """
        # Determine all tickers needed to fetch at once
        trend_inputs = self.signals.get("trend", {}).get(
            "inputs",
            ["SPY"],
        )

        trend_proxy = trend_inputs[0]
        volatility_inputs = self.signals.get(
            "volatility",
            {},
        ).get(
            "inputs",
            ["^VIX"],
        )

        vix = volatility_inputs[0]
        leaders = self.signals.get("leadership", {}).get("proxies", ["SMH", "QQQ"])
        credit = self.signals.get("credit", {}).get("proxies", ["JNK", "SHY"])

        breadth_config = self.signals.get("breadth", {})

        breadth_inputs = breadth_config.get(
            "inputs",
            BreadthSignal.DEFAULT_PROXIES,
        )

        all_tickers = list(
            set(
                [trend_proxy, vix]
                + leaders
                + credit
                + breadth_inputs
            )
        )

        # 1. Fetch Data
        closes = self._fetch_daily_closes(all_tickers, period="1y")

        # Prepare signal results log
        results = {
            "trend": {"status": "Unknown", "value": 0, "dma200": 0, "dma50": 0},
            "breadth": {
                "status": "Unknown",
                "value": 0,
                "passing": [],
                "failing": [],
                "valid_total": 0,
            },
            "volatility": {"status": "Unknown", "value": 0},
            "leadership": {"status": "Unknown", "value": 0},
            "credit": {"status": "Unknown", "value": 0},
            "regime": "TRANSITION",
            "score": 0,
        }

        if closes.empty:
            return results

        # Calculate latest values and moving averages safely
        latest = closes.iloc[-1]
        try:
            dma50 = closes.rolling(window=50).mean().iloc[-1]
            dma200 = closes.rolling(window=200).mean().iloc[-1]
        except Exception:
            return results

        # 2. Evaluate Trend
        if trend_proxy in closes.columns:
            trend_signal = TrendSignal(self.signals.get("trend", {}))

            results["trend"] = trend_signal.evaluate(
                {
                    "current": latest[trend_proxy],
                    "dma50": dma50[trend_proxy],
                    "dma200": dma200[trend_proxy],
                }
            )

        # 3. Evaluate Breadth
        breadth_signal = BreadthSignal(
            self.signals.get("breadth", {})
        )

        results["breadth"] = breadth_signal.evaluate(
            {
                "latest": latest,
                "dma50": dma50,
            }
        )

        # 4. Evaluate Volatility
        if vix in closes.columns:
            volatility_signal = VolatilitySignal(
                self.signals.get("volatility", {})
            )

            results["volatility"] = volatility_signal.evaluate(
                {
                    "value": latest[vix],
                }
            )

        # 5. Evaluate Leadership
        smh = "SMH"
        qqq = "QQQ"
        if smh in closes.columns and qqq in closes.columns:
            results["leadership"]["qqq"] = latest[qqq]
            results["leadership"]["qqq_50"] = dma50[qqq]
            results["leadership"]["smh"] = latest[smh]
            results["leadership"]["smh_50"] = dma50[smh]
            results["leadership"]["status"] = self.get_leadership_signal(
                latest[qqq], dma50[qqq], latest[smh], dma50[smh]
            )

        # 6. Evaluate Credit
        if "JNK" in closes.columns and "SHY" in closes.columns:
            jnk_price = latest["JNK"]
            shy_price = latest["SHY"]
            jnk_50 = dma50["JNK"]
            shy_50 = dma50["SHY"]

            results["credit"]["jnk"] = jnk_price
            results["credit"]["shy"] = shy_price
            results["credit"]["ratio_current"] = (
                jnk_price / shy_price if shy_price > 0 else 0
            )
            results["credit"]["ratio_50"] = jnk_50 / shy_50 if shy_50 > 0 else 0

            results["credit"]["status"] = self.get_credit_signal(
                jnk_price, shy_price, jnk_50, shy_50
            )

        # 7. Regime Scoring Logic
        # Calculate strictness: we assign points to signals.
        # Trend: Bullish=2, Neutral=1, Bearish=0
        # Breadth: Strong=2, Improving=1, Weak=0
        # Volatility: Calm=2, Neutral=1, Risk-off=0
        # Leadership: Strong=2, Mixed=1, Weak=0
        # Credit: Healthy=2, Stressed=0

        points = 0
        if results["trend"]["status"] == "Bullish":
            points += 2
        elif results["trend"]["status"] == "Neutral":
            points += 1

        if results["breadth"]["status"] == "Strong":
            points += 2
        elif results["breadth"]["status"] == "Improving":
            points += 1

        if results["volatility"]["status"] == "Calm":
            points += 2
        elif results["volatility"]["status"] == "Neutral":
            points += 1

        if results["leadership"]["status"] == "Strong":
            points += 2
        elif results["leadership"]["status"] == "Mixed":
            points += 1

        if results["credit"]["status"] == "Healthy":
            points += 2

        results["score"] = points

        # Max 10 points
        # Risk-On: >= 7 points
        # Defensive: <= 3 points
        # Transition: 4 to 6 points

        if points >= 7:
            results["regime"] = "RISK_ON"
        elif points <= 3:
            results["regime"] = "DEFENSIVE"
        else:
            results["regime"] = "TRANSITION"

        return results
