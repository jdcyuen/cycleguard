import pytest

from engine.allocation.dynamic_allocation_strategy import DynamicAllocationStrategy


def test_dynamic_allocation_strategy_is_abstract():
    with pytest.raises(TypeError):
        DynamicAllocationStrategy()