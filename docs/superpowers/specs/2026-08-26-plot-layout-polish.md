# Plot Layout Polish Specification

## Scope

Polish the existing anaStruct Plus plotting layer without changing anaStruct's solver, structural results, public modelling API, or the physical-axis semantics introduced in v0.2.3.

## Requirements

1. `show_structure()` must keep both geometric axes (`x` and `y`) because both are physical coordinates.
2. Native node IDs and element IDs must remain visible, but must be visually distinguishable from one another and from loads/results.
3. Node IDs must use a blue visual treatment; element IDs must use a green visual treatment. Both must use a small white background box and bold text for legibility.
4. Node and element ID labels must be moved away from the structural line using screen-space offsets so they do not sit directly on the member, support, or load arrows.
5. Label placement must work for horizontal beams and remain geometry-driven for general 2D frames: node labels move outward from the model centroid; element labels move normal to the member, preferably away from the model centroid.
6. Result figures must preserve the physically honest axis policy from v0.2.3: only the true longitudinal coordinate remains numeric for a one-direction model; scaled transverse plotting coordinates never appear as physical values.
7. Result plots must receive additional visual breathing room so supports, extrema labels, reaction labels, titles, and callouts are not flush with or clipped by the axes/figure edges.
8. `show_displacement()` must identify the real maximum-displacement annotation close to its plotted location using a leader arrow. The label must read `u_max = <value> <length_unit>` when one native maximum is present.
9. The displacement callout anchor must point to the nearest point on the plotted deformed curve, not to a remote corner or generic axes position.
10. Existing `values_only=True` behavior and all existing numerical annotations for moment, shear, axial force, and reactions must remain unchanged.
11. No new runtime dependency is permitted.
12. Version after completion: `0.2.4`.

## Acceptance criteria

- The reference 4 m fixed-pinned beam with `q=-10` shows node IDs and element ID in distinct colors and with no overlap with the member line or the centered `q` label.
- Moment, shear, reactions, and displacement have visibly larger margins than v0.2.3 while retaining compact framing.
- `u_max = 0.003 m` appears close to the maximum-deformation region and a visible arrow terminates at the deformed curve.
- Existing axis-semantics tests remain green.
- New layout tests cover ID styling, label/geometry separation, figure margin expansion, and the displacement arrow anchor.
