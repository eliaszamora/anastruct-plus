import matplotlib.pyplot as plt

from test_anastruct_plus import Node, SystemElementsPlus


def test_horizontal_result_plots_keep_only_real_longitudinal_axis():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    for method in (
        ss.show_shear_force,
        ss.show_bending_moment,
        ss.show_axial_force,
        ss.show_reaction_force,
        ss.show_displacement,
    ):
        fig = method(show=False)
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
