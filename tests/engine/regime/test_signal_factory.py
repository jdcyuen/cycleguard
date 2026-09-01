import pytest

from engine.regime.signal_factory import SignalFactory
from engine.regime.signals.trend import TrendSignal
from engine.regime.signals.breadth import BreadthSignal
from engine.regime.signals.volatility import VolatilitySignal
from engine.regime.signals.leadership import LeadershipSignal
from engine.regime.signals.credit import CreditSignal
from engine.regime.signals.cape import CapeSignal


def test_create_trend_signal():
    signal = SignalFactory.create("trend", {})
    assert isinstance(signal, TrendSignal)


def test_create_breadth_signal():
    signal = SignalFactory.create("breadth", {})
    assert isinstance(signal, BreadthSignal)


def test_create_volatility_signal():
    signal = SignalFactory.create("volatility", {})
    assert isinstance(signal, VolatilitySignal)


def test_create_leadership_signal():
    signal = SignalFactory.create("leadership", {})
    assert isinstance(signal, LeadershipSignal)


def test_create_credit_signal():
    signal = SignalFactory.create("credit", {})
    assert isinstance(signal, CreditSignal)


def test_create_cape_signal():
    signal = SignalFactory.create("cape", {})
    assert isinstance(signal, CapeSignal)


def test_unknown_signal_raises_error():
    with pytest.raises(ValueError, match="Unknown signal"):
        SignalFactory.create("unknown", {})