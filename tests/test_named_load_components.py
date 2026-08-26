import subprocess
import sys
import textwrap


BASE = r'''
import matplotlib
matplotlib.use("Agg")
import numpy as np
from anastruct_plus import SystemElements


def model():
    ss = SystemElements(force_unit="tonf", length_unit="m")
    ss.add_element(location=[[0, 0], [4, 0]])
    ss.add_support_fixed(node_id=1)
    ss.add_support_hinged(node_id=2)
    return ss


def results(ss):
    ss.solve()
    data = ss.get_element_results(element_id=1, verbose=True)
    if isinstance(data, list):
        data = data[0]
    return np.asarray(data["Q"], dtype=float), np.asarray(data["M"], dtype=float)
'''


def run_isolated(assertions: str) -> None:
    code = BASE + "\n" + textwrap.dedent(assertions)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_named_components_in_one_call_match_direct_resultant():
    run_isolated(
        '''
        direct = model()
        direct.q_load(element_id=1, q=-15)
        q_direct, m_direct = results(direct)

        named = model()
        named.q_load(element_id=1, pp_c=-5, sc_c=-10)
        q_named, m_named = results(named)

        assert np.allclose(q_named, q_direct)
        assert np.allclose(m_named, m_direct)
        '''
    )


def test_named_components_in_separate_calls_accumulate():
    run_isolated(
        '''
        direct = model()
        direct.q_load(element_id=1, q=-15)
        q_direct, m_direct = results(direct)

        named = model()
        named.q_load(element_id=1, pp_c=-5)
        named.q_load(element_id=1, sc_c=-10)
        q_named, m_named = results(named)

        assert np.allclose(q_named, q_direct)
        assert np.allclose(m_named, m_direct)
        '''
    )


def test_structure_plot_shows_components_and_resultant():
    run_isolated(
        '''
        ss = model()
        ss.q_load(element_id=1, pp_c=-5, sc_c=-10)
        fig = ss.show_structure(show=False)
        labels = [text.get_text() for text in fig.axes[0].texts]

        assert any("pp_c = 5.0 tonf/m" in label for label in labels), labels
        assert any("sc_c = 10.0 tonf/m" in label for label in labels), labels
        assert any("Σq = 15.0 tonf/m" in label for label in labels), labels
        '''
    )


def test_traditional_q_load_keeps_anastruct_replace_semantics():
    run_isolated(
        '''
        repeated = model()
        repeated.q_load(element_id=1, q=-4)
        repeated.q_load(element_id=1, q=-3)
        q_repeated, m_repeated = results(repeated)

        direct = model()
        direct.q_load(element_id=1, q=-3)
        q_direct, m_direct = results(direct)

        assert np.allclose(q_repeated, q_direct)
        assert np.allclose(m_repeated, m_direct)
        '''
    )


def test_named_components_cannot_be_mixed_with_q_in_same_call():
    run_isolated(
        '''
        ss = model()
        try:
            ss.q_load(element_id=1, q=-15, pp_c=-5, sc_c=-10)
        except ValueError as exc:
            assert "q" in str(exc)
        else:
            raise AssertionError("Expected ValueError when mixing q and named components")
        '''
    )
