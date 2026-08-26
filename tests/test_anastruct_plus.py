import sys
import types

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class Vertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Node:
    def __init__(self, x, y, node_id=0, Fx=0.0, Fy=0.0, Tz=0.0):
        self.id = node_id
        self.vertex = Vertex(x, y)
        self.Fx = Fx
        self.Fy = Fy
        self.Tz = Tz


class Element:
    def __init__(self, eid=1):
        self.id = eid
        self.type = "general"
        self.bending_moment = np.array([20.0, 8.0, -5.0, -11.2, 0.0])
        self.shear_force = np.array([25.0, 15.0, 5.0, -5.0, -15.0])
        self.axial_force = np.array([4.0, 4.0, 4.0, 4.0, 4.0])
        self.vertex_1 = Vertex(0.0, 0.0)
        self.vertex_2 = Vertex(4.0, 0.0)


class FakeSystemElements:
    def __init__(self, *args, figsize=(12, 8), **kwargs):
        self.figsize = figsize
        self.node_map = {1: Node(0, 0, 1), 2: Node(4, 0, 2)}
        self.element_map = {1: Element(1)}
        self.orientation_cs = -1
        self.reaction_forces = {
            1: Node(0, 0, 1, Fx=0.0, Fy=-25.0, Tz=20.0),
            2: Node(4, 0, 2, Fx=0.0, Fy=-15.0, Tz=0.0),
        }

    def get_element_results(self, element_id=None, verbose=False):
        data = {
            "id": 1,
            "length": 4.0,
            "M": self.element_map[1].bending_moment if verbose else None,
            "Q": self.element_map[1].shear_force if verbose else None,
            "N": self.element_map[1].axial_force if verbose else None,
        }
        return data if element_id else [data]

    def _coords(self, key):
        values = {
            "M": self.element_map[1].bending_moment,
            "Q": self.element_map[1].shear_force,
            "N": self.element_map[1].axial_force,
        }[key]
        x = np.linspace(0, 4, len(values))
        y = values / max(1.0, np.max(np.abs(values))) * 0.6
        return np.r_[0.0, x, 4.0], np.r_[0.0, y, 0.0]

    @staticmethod
    def _wide_axes(ax):
        ax.set_xlim(-2, 6)
        ax.set_ylim(-1, 1)

    def _figure(self, key, figsize):
        fig, ax = plt.subplots(figsize=figsize)
        x, y = self._coords(key)
        ax.plot(x, y)
        ax.plot([0, 4], [0, 0])
        self._wide_axes(ax)
        return fig

    def show_structure(
        self,
        verbosity=0,
        scale=1.0,
        offset=(0, 0),
        figsize=None,
        show=True,
        supports=True,
        values_only=False,
        annotations=False,
    ):
        if values_only:
            return np.array([0.0, 4.0]), np.array([0.0, 0.0])
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot([0, 4], [0, 0])
        if verbosity == 0:
            ax.text(0, 0.2, "q=10.0")
            ax.text(4, 0.2, "q=10.0")
            ax.text(2, 0.16, "1")
        self._wide_axes(ax)
        if show:
            plt.show()
            return None
        return fig

    def show_bending_moment(
        self,
        factor=None,
        verbosity=0,
        scale=1,
        offset=(0, 0),
        figsize=None,
        show=True,
        values_only=False,
    ):
        if values_only:
            return self._coords("M")
        fig = self._figure("M", figsize)
        if show:
            plt.show()
            return None
        return fig

    def show_shear_force(
        self,
        factor=None,
        verbosity=0,
        scale=1,
        offset=(0, 0),
        figsize=None,
        show=True,
        values_only=False,
    ):
        if values_only:
            return self._coords("Q")
        fig = self._figure("Q", figsize)
        if show:
            plt.show()
            return None
        return fig

    def show_axial_force(
        self,
        factor=None,
        verbosity=0,
        scale=1,
        offset=(0, 0),
        figsize=None,
        show=True,
        values_only=False,
    ):
        if values_only:
            return self._coords("N")
        fig = self._figure("N", figsize)
        if show:
            plt.show()
            return None
        return fig

    def show_reaction_force(
        self,
        verbosity=0,
        scale=1,
        offset=(0, 0),
        figsize=None,
        show=True,
    ):
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot([0, 4], [0, 0])
        ax.annotate("", xy=(0, 0), xytext=(0, -0.6), arrowprops={"arrowstyle": "->"})
        ax.annotate("", xy=(4, 0), xytext=(4, -0.4), arrowprops={"arrowstyle": "->"})
        if verbosity == 0:
            ax.text(0, -0.8, "R=-25.0")
            ax.text(0.15, 0.15, "T=20.0")
            ax.text(4, -0.6, "R=-15.0")
        self._wide_axes(ax)
        if show:
            plt.show()
            return None
        return fig

    def show_displacement(
        self,
        factor=None,
        verbosity=0,
        scale=1,
        offset=(0, 0),
        figsize=None,
        show=True,
        linear=False,
        values_only=False,
    ):
        x = np.linspace(0, 4, 5)
        y = np.array([0.0, -0.25, -0.55, -0.35, 0.0])
        if values_only:
            return x, y
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot([0, 4], [0, 0])
        ax.plot(x, y)
        if verbosity == 0:
            ax.text(2.15, -0.62, "0.003")
        self._wide_axes(ax)
        if show:
            plt.show()
            return None
        return fig


fake_anastruct = types.ModuleType("anastruct")
fake_anastruct.SystemElements = FakeSystemElements
sys.modules["anastruct"] = fake_anastruct

from anastruct_plus import SystemElementsPlus


def texts(fig):
    return [t.get_text() for t in fig.axes[0].texts]


def test_auto_figsize_is_compact_for_horizontal_beam():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    width, height = ss._auto_figsize()
    assert width >= 8
    assert height <= 3.5


def test_structure_adds_units_collapses_uniform_q_and_tightens_axes():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_structure(show=False)
    ax = fig.axes[0]
    assert ax.get_xlabel() == "x [m]"
    assert ax.get_ylabel() == "y [m]"
    assert texts(fig).count("q=10.0 tonf/m") == 1
    q_label = next(t for t in ax.texts if t.get_text() == "q=10.0 tonf/m")
    element_label = next(t for t in ax.texts if t.get_text() == "1")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert not q_label.get_window_extent(renderer).overlaps(element_label.get_window_extent(renderer))
    assert ax.get_xlim()[0] > -1.0
    assert ax.get_xlim()[1] < 5.0


def test_bending_moment_labels_endpoints_and_global_extrema_including_zero_end():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    labels = texts(fig)
    assert "20.00 tonf·m" in labels
    assert "0.00 tonf·m" in labels
    assert "-11.20 tonf·m" in labels
    assert fig.axes[0].get_title() == "Diagrama de momento flector [tonf·m]"


def test_bending_moment_does_not_duplicate_same_index():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    labels = texts(fig)
    assert labels.count("20.00 tonf·m") == 1
    assert labels.count("0.00 tonf·m") == 1
    assert labels.count("-11.20 tonf·m") == 1


def test_shear_force_labels_endpoints_and_extrema():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_shear_force(show=False)
    labels = texts(fig)
    assert "25.00 tonf" in labels
    assert "-15.00 tonf" in labels
    assert fig.axes[0].get_title() == "Diagrama de esfuerzo cortante [tonf]"


def test_axial_force_uses_force_unit_and_avoids_repeated_constant_labels():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_axial_force(show=False)
    labels = texts(fig)
    assert labels.count("4.00 tonf") == 2
    assert fig.axes[0].get_title() == "Diagrama de fuerza axial [tonf]"


def test_force_diagrams_use_tight_geometry_bounds():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    for method in (ss.show_shear_force, ss.show_bending_moment, ss.show_axial_force):
        fig = method(show=False)
        xmin, xmax = fig.axes[0].get_xlim()
        assert xmin > -1.0
        assert xmax < 5.0


def test_reaction_force_has_units_clear_labels_and_auto_framing():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_reaction_force(show=False)
    labels = texts(fig)
    assert fig.axes[0].get_title() == "Diagrama de reacciones"
    assert "R1y = 25.00 tonf" in labels
    assert "M1 = 20.00 tonf·m" in labels
    assert "R2y = 15.00 tonf" in labels
    assert not any(label.startswith("R=") or label.startswith("T=") for label in labels)
    r1 = next(t for t in fig.axes[0].texts if t.get_text() == "R1y = 25.00 tonf")
    m1 = next(t for t in fig.axes[0].texts if t.get_text() == "M1 = 20.00 tonf·m")
    assert abs(m1.get_position()[1] - r1.get_position()[1]) >= 16
    r2 = next(t for t in fig.axes[0].texts if t.get_text() == "R2y = 15.00 tonf")
    assert r2.get_ha() == "right"
    xmin, xmax = fig.axes[0].get_xlim()
    assert xmin > -1.0
    assert xmax < 5.0


def test_reaction_vertical_sign_respects_non_inverted_coordinates():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    ss.orientation_cs = 1
    fig = ss.show_reaction_force(show=False)
    labels = texts(fig)
    assert "R1y = -25.00 tonf" in labels
    assert "R2y = -15.00 tonf" in labels


def test_displacement_has_unit_identified_value_and_auto_framing():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_displacement(show=False)
    labels = texts(fig)
    assert fig.axes[0].get_title() == "Forma deformada (escala amplificada)"
    assert "u_max = 0.003 m" in labels
    assert "0.003" not in labels
    u_label = next(t for t in fig.axes[0].texts if t.get_text() == "u_max = 0.003 m")
    assert hasattr(u_label, "xy")
    assert abs(u_label.get_position()[1]) >= 10
    xmin, xmax = fig.axes[0].get_xlim()
    assert xmin > -1.0
    assert xmax < 5.0


def test_displacement_values_only_preserves_native_api():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    x, y = ss.show_displacement(values_only=True)
    assert len(x) == 5
    assert len(y) == 5


def test_values_only_preserves_native_api():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    x, y = ss.show_bending_moment(values_only=True)
    assert len(x) == 7
    assert len(y) == 7


def test_show_structure_emits_no_layout_warning():
    import warnings

    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ss.show_structure(show=False)
    assert caught == []


def test_annotation_cursor_stays_aligned_when_truss_has_no_moment_results():
    class Truss(Element):
        def __init__(self, eid=1):
            super().__init__(eid)
            self.type = "truss"
            self.bending_moment = np.zeros(5)

    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    truss = Truss(1)
    beam = Element(2)
    beam.vertex_1 = Vertex(4.0, 0.0)
    beam.vertex_2 = Vertex(8.0, 0.0)
    ss.element_map = {1: truss, 2: beam}

    def results(element_id=None, verbose=False):
        return [
            {"id": 1, "length": 4.0, "M": None, "Q": None, "N": truss.axial_force},
            {
                "id": 2,
                "length": 4.0,
                "M": beam.bending_moment,
                "Q": beam.shear_force,
                "N": beam.axial_force,
            },
        ]

    ss.get_element_results = results
    x = np.r_[np.linspace(0, 4, 7), np.linspace(4, 8, 7)]
    y = np.r_[np.zeros(7), np.array([0, 0.6, 0.2, -0.1, -0.3, 0, 0])]
    fig, _ = plt.subplots()
    ss._annotate_relevant_values(fig, "M", x, y, 2)
    annotations = fig.axes[0].texts
    first = next(t for t in annotations if t.get_text() == "20.00 tonf·m")
    assert first.xy[0] > 4.0
