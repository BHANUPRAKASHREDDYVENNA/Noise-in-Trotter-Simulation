import numpy as np

from src.bell_benchmark import bell_state, bell_correlations, proportion_standard_error


def test_bell_state_correlations():
    state = bell_state()
    corr = bell_correlations(state)
    assert np.isclose(corr["XX"], 1.0)
    assert np.isclose(corr["YY"], -1.0)
    assert np.isclose(corr["ZZ"], 1.0)


def test_standard_error():
    assert np.isclose(proportion_standard_error(0.92, 2048), np.sqrt(0.92 * 0.08 / 2048))
