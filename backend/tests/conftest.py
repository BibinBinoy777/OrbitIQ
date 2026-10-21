"""Scientific boundary guards independent of optional application features."""

import sys
from types import ModuleType

import orbitiq
import pytest


@pytest.fixture
def forbid_swarm_residuals(monkeypatch):
    """Retain the same failure guard in full and scoped publication checkouts.

    An optional unpublished observation feature must not be a collection-time
    dependency of offline source diagnostics. If absent, install a test-only
    sentinel: any attempted residual call still fails, rather than being skipped.
    """

    def forbidden(*args, **kwargs):
        raise AssertionError("Swarm residual evaluation forbidden during qualification")

    name = "orbitiq.observation_validation"
    module = sys.modules.get(name)
    if module is None:
        module = ModuleType(name)
        monkeypatch.setitem(sys.modules, name, module)
        monkeypatch.setattr(orbitiq, "observation_validation", module, raising=False)
    monkeypatch.setattr(module, "residual", forbidden, raising=False)
    return forbidden
