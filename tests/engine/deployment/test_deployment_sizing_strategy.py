from decimal import Decimal

import pytest

from engine.deployment.deployment_sizing_strategy import (
    DeploymentSizingStrategy,
)


def test_deployment_sizing_strategy_requires_calculate():
    with pytest.raises(TypeError):
        DeploymentSizingStrategy()