import matplotlib.pyplot as plt

from test_anastruct_plus import FakeSystemElements, Node, SystemElementsPlus


def test_horizontal_internal_force_plots_use_physical_transverse_axis():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    for method, ylabel in (
        (ss.show_shear_force, "V [tonf]"),
        (ss.show_bending_moment, "M [tonf·m]"),
        (ss.show_axial_force, "N [tonf]"),
    ):
        fig = method(show=False)
        ax = fig.axes[0]
        assert ax.get_xlabel() == "x [m]"
        assert ax.get_ylabel() == ylabel
        assert len(ax.get_yticks()) > 0
        plt.close(fig)


def test_horizontal_displacement_uses_physical_transverse_axis():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_displacement(show=False)
    ax = fig.axes[0]
    assert ax.get_xlabel() == "x [m]"
    assert ax.get_ylabel() == "u_y [m]"
    assert len(ax.get_yticks()) > 0
    plt.close(fig)


def test_horizontal_reaction_plot_does_not_claim_false_transverse_scale():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_reaction_force(show=False)
    ax = fig.axes[0]
    assert ax.get_xlabel() == "x [m]"
    assert ax.get_ylabel() == ""
    assert len(ax.get_yticks()) == 0
    plt.close(fig)


def test_vertical_result_plot_keeps_only_real_longitudinal_axis():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    ss.node_map = {1: Node(0, 0, 1), 2: Node(0, 4, 2)}
    fig = ss.show_bending_moment(show=False)
    ax = fig.axes[0]
    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == "y [m]"
    assert len(ax.get_xticks()) == 0
    plt.close(fig)


def test_frame_result_plot_hides_both_scaled_coordinate_axes():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    ss.node_map = {
        1: Node(0, 0, 1),
        2: Node(4, 0, 2),
        3: Node(4, 3, 3),
    }
    fig = ss.show_bending_moment(show=False)
    ax = fig.axes[0]
    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == ""
    assert len(ax.get_xticks()) == 0
    assert len(ax.get_yticks()) == 0
    plt.close(fig)


def test_structure_ids_are_distinct_prefixed_and_offset_from_geometry(monkeypatch):
    native_show_structure = FakeSystemElements.show_structure

    def show_structure_with_node_ids(self, *args, **kwargs):
        requested_show = kwargs.get("show", True)
        requested_values = kwargs.get("values_only", False)
        if requested_values:
            return native_show_structure(self, *args, **kwargs)
        kwargs["show"] = False
        fig = native_show_structure(self, *args, **kwargs)
        ax = fig.axes[0]
        ax.text(0.08, 0.07, "1")
        ax.text(4.08, 0.07, "2")
        if requested_show:
            plt.show()
            return None
        return fig

    monkeypatch.setattr(FakeSystemElements, "show_structure", show_structure_with_node_ids)

    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_structure(show=False)
    ax = fig.axes[0]

    node_labels = [
        t for t in ax.texts if getattr(t, "_anastruct_plus_kind", None) == "node"
    ]
    element_labels = [
        t for t in ax.texts if getattr(t, "_anastruct_plus_kind", None) == "element"
    ]

    assert len(node_labels) == 2
    assert len(element_labels) == 1
    assert {t.get_text() for t in node_labels} == {"N1", "N2"}
    assert {t.get_text() for t in element_labels} == {"E1"}
    assert all(t.get_color() == "tab:blue" for t in node_labels)
    assert all(t.get_color() == "tab:green" for t in element_labels)
    assert all(t.get_fontweight() == "bold" for t in node_labels + element_labels)
    assert all(t.get_bbox_patch() is not None for t in node_labels + element_labels)
    assert all(hasattr(t, "xy") for t in node_labels + element_labels)
    assert all(t.get_position() != (0, 0) for t in node_labels + element_labels)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    q_label = next(t for t in ax.texts if t.get_text() == "q=10.0 tonf/m")
    for label in node_labels + element_labels:
        anchor = ax.transData.transform(label.xy)
        assert not label.get_window_extent(renderer).contains(*anchor)
    for label in element_labels:
        assert not label.get_window_extent(renderer).overlaps(
            q_label.get_window_extent(renderer)
        )
    plt.close(fig)


def test_result_plots_have_extra_breathing_room_and_outer_layout():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    ax = fig.axes[0]
    xmin, xmax = ax.get_xlim()
    position = ax.get_position()

    assert xmin < -0.45
    assert xmax > 4.45
    assert position.y0 >= 0.17
    assert position.y1 <= 0.87
    plt.close(fig)


def test_displacement_max_is_nearby_arrow_callout_to_curve():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_displacement(show=False)
    ax = fig.axes[0]
    label = next(
        t
        for t in ax.texts
        if getattr(t, "_anastruct_plus_kind", None) == "displacement_max"
    )

    assert label.get_text() == "u_max = 0.003 m"
    assert getattr(label, "arrow_patch", None) is not None
    assert hasattr(label, "xy")
    dx, dy = label.get_position()
    assert abs(dx) <= 24
    assert abs(dy) <= 24

    x_anchor, y_anchor = label.xy
    nearest_d2 = float("inf")
    for line in ax.lines:
        xs = line.get_xdata()
        ys = line.get_ydata()
        if len(xs) < 3 or len(xs) != len(ys):
            continue
        nearest_d2 = min(
            nearest_d2,
            min((float(x) - x_anchor) ** 2 + (float(y) - y_anchor) ** 2 for x, y in zip(xs, ys)),
        )
    assert nearest_d2 < 1e-12
    plt.close(fig)
