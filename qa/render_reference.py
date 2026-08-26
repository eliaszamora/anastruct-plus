from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from anastruct_plus import SystemElements


OUTPUT = Path("qa_output")
OUTPUT.mkdir(exist_ok=True)

ss = SystemElements(force_unit="tonf", length_unit="m")
ss.add_element(location=[[0, 0], [4, 0]])
ss.add_support_fixed(node_id=1)
ss.add_support_hinged(node_id=2)
ss.q_load(element_id=1, q=-10)

plots = [("01_structure", lambda: ss.show_structure(show=False))]

structure_fig = plots[0][1]()
structure_fig.savefig(OUTPUT / "01_structure.png", dpi=150, bbox_inches="tight")
plt.close(structure_fig)

ss.solve()

for name, method in (
    ("02_reactions", ss.show_reaction_force),
    ("03_shear", ss.show_shear_force),
    ("04_moment", ss.show_bending_moment),
    ("05_displacement", ss.show_displacement),
):
    fig = method(show=False)
    fig.savefig(OUTPUT / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

named = SystemElements(force_unit="tonf", length_unit="m")
named.add_element(location=[[0, 0], [4, 0]])
named.add_support_fixed(node_id=1)
named.add_support_hinged(node_id=2)
named.q_load(element_id=1, pp_c=-5, sc_c=-10)

fig = named.show_structure(show=False)
fig.savefig(OUTPUT / "06_named_load_components.png", dpi=150, bbox_inches="tight")
plt.close(fig)
