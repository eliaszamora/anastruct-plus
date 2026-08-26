import matplotlib.pyplot as plt

from test_anastruct_plus import Node, SystemElementsPlus, texts


def test_horizontal_result_plot_keeps_left_frame_spine_visible():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    ax = fig.axes[0]
    assert len(ax.get_yticks()) == 0
    assert ax.spines["left"].get_visible()
    plt.close(fig)


def test_vertical_result_plot_keeps_bottom_frame_spine_visible():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    ss.node_map = {1: Node(0, 0, 1), 2: Node(0, 4, 2)}
    fig = ss.show_bending_moment(show=False)
    ax = fig.axes[0]
    assert len(ax.get_xticks()) == 0
    assert ax.spines["bottom"].get_visible()
    plt.close(fig)


def test_bending_moment_annotations_include_moment_unit():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    labels = texts(fig)
    assert "20.00 tonf·m" in labels
    assert "0.00 tonf·m" in labels
    assert "-11.20 tonf·m" in labels
    plt.close(fig)


def test_shear_annotations_include_force_unit():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_shear_force(show=False)
    labels = texts(fig)
    assert "25.00 tonf" in labels
    assert "-15.00 tonf" in labels
    plt.close(fig)


def test_axial_annotations_include_force_unit():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_axial_force(show=False)
    labels = texts(fig)
    assert labels.count("4.00 tonf") == 2
    plt.close(fig)
