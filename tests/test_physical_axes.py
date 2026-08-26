import subprocess
import sys
import textwrap


BASE = r'''
import matplotlib
matplotlib.use("Agg")
import numpy as np
from anastruct_plus import SystemElements

ss = SystemElements(force_unit="tonf", length_unit="m")
ss.add_element(location=[[0, 0], [4, 0]])
ss.add_support_fixed(node_id=1)
ss.add_support_hinged(node_id=2)
ss.q_load(element_id=1, q=-10)
ss.solve()

def tick_map(ax):
    mapping = {}
    for position, label in zip(ax.get_yticks(), ax.get_yticklabels()):
        raw = label.get_text().strip()
        if raw:
            mapping[float(raw)] = float(position)
    return mapping
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


def test_structure_ids_use_explicit_node_and_element_prefixes():
    run_isolated(
        '''
        fig = ss.show_structure(show=False)
        labels = {text.get_text() for text in fig.axes[0].texts}
        assert "N1" in labels
        assert "N2" in labels
        assert "E1" in labels
        '''
    )


def test_shear_uses_physical_vertical_axis():
    run_isolated(
        '''
        fig = ss.show_shear_force(show=False)
        ax = fig.axes[0]
        assert ax.get_ylabel() == "V [tonf]"
        ticks = tick_map(ax)
        assert -25.0 in ticks
        assert 15.0 in ticks
        annotations = {text.get_text(): text for text in ax.texts}
        assert np.isclose(annotations["-25.00 tonf"].xy[1], ticks[-25.0])
        assert np.isclose(annotations["15.00 tonf"].xy[1], ticks[15.0])
        assert ax.yaxis.get_gridlines()
        '''
    )


def test_moment_uses_physical_vertical_axis():
    run_isolated(
        '''
        fig = ss.show_bending_moment(show=False)
        ax = fig.axes[0]
        assert ax.get_ylabel() == "M [tonf·m]"
        ticks = tick_map(ax)
        assert 20.0 in ticks
        annotations = {text.get_text(): text for text in ax.texts}
        assert np.isclose(annotations["20.00 tonf·m"].xy[1], ticks[20.0])
        assert any(value < 0 for value in ticks)
        '''
    )


def test_displacement_uses_physical_vertical_axis():
    run_isolated(
        '''
        fig = ss.show_displacement(show=False)
        ax = fig.axes[0]
        assert ax.get_ylabel() == "u_y [m]"
        tick_values = sorted(tick_map(ax))
        assert tick_values[0] < 0.0
        assert 0.0 in tick_values
        assert any(text.get_text().startswith("u_max = ") for text in ax.texts)
        '''
    )


def test_reactions_do_not_claim_a_false_transverse_physical_scale():
    run_isolated(
        '''
        fig = ss.show_reaction_force(show=False)
        ax = fig.axes[0]
        assert ax.get_ylabel() == ""
        assert len(ax.get_yticks()) == 0
        '''
    )
