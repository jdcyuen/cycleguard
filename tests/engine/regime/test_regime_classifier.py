from engine.regime.regime_classifier import RegimeClassifier


REGIME_CONFIG = {
    "regimes": {
        "RISK_ON": {
            "conditions": {
                "trend": "bullish",
                "breadth": "strong",
                "volatility": "calm",
            }
        },
        "TRANSITION": {
            "conditions": {
                "trend": "neutral",
                "breadth": "neutral",
            }
        },
        "DEFENSIVE": {
            "conditions": {
                "trend": "bearish",
                "volatility": "elevated",
            }
        },
        "CRISIS": {
            "conditions": {
                "volatility": "stress",
                "breadth": "weak",
            }
        },
    },
    "fallback_regime": "TRANSITION",
}


def test_classifies_risk_on():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "trend": {"status": "bullish"},
            "breadth": {"status": "strong"},
            "volatility": {"status": "calm"},
        }
    )

    assert result == "RISK_ON"


def test_classifies_transition():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "trend": {"status": "neutral"},
            "breadth": {"status": "neutral"},
        }
    )

    assert result == "TRANSITION"


def test_classifies_defensive():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "trend": {"status": "bearish"},
            "volatility": {"status": "elevated"},
        }
    )

    assert result == "DEFENSIVE"


def test_classifies_crisis():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "volatility": {"status": "stress"},
            "breadth": {"status": "weak"},
        }
    )

    assert result == "CRISIS"


def test_uses_fallback_when_no_regime_matches():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "trend": {"status": "bullish"},
            "breadth": {"status": "weak"},
            "volatility": {"status": "neutral"},
        }
    )

    assert result == "TRANSITION"


def test_all_conditions_must_match():
    classifier = RegimeClassifier(REGIME_CONFIG)

    result = classifier.classify(
        {
            "trend": {"status": "bullish"},
            "breadth": {"status": "neutral"},
            "volatility": {"status": "calm"},
        }
    )

    assert result == "TRANSITION"