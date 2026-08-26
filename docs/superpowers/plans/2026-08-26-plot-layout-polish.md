# Plot Layout Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make anaStruct Plus plots visually legible and non-cropped while keeping v0.2.3's physically honest axes and the existing structural-analysis API unchanged.

**Architecture:** Keep `anastruct_plus/system.py` as the core plotting/post-processing layer and implement this revision only in `anastruct_plus/axis_semantics.py`, the current public subclass. Add small geometry-aware label-placement and figure-padding helpers there. Tests use the existing fake anaStruct backend, so every visual rule is testable without changing or mocking the solver itself.

**Tech Stack:** Python 3.10+, anaStruct >=1.7.0, Matplotlib >=3.7, NumPy >=1.24, pytest.

**Spec:** `docs/superpowers/specs/2026-08-26-plot-layout-polish.md`

## Global Constraints

- Do not change anaStruct's solver or structural results.
- Do not add runtime dependencies.
- Preserve `values_only=True` behavior.
- Preserve v0.2.3 physical-axis semantics.
- Node IDs: blue; element IDs: green; both bold with white background boxes.
- Displacement maximum must be a nearby arrow callout anchored to the deformed curve.
- Target package version: `0.2.4`.

---

### Task 1: Geometry-aware structure ID labels

**Files:**
- Modify: `anastruct_plus/axis_semantics.py`
- Test: `tests/test_axis_semantics.py`

**Interfaces:**
- Consumes: `SystemElementsPlus.node_map`, `SystemElementsPlus.element_map`, Matplotlib `Text` artists returned by `show_structure()`.
- Produces: `_style_structure_ids(fig) -> None`, `_node_label_offset(node) -> tuple[float, float]`, `_element_label_offset(element) -> tuple[float, float]`.

- [ ] **Step 1: Write failing tests for color, box, and separation**

```python
def test_structure_ids_are_distinct_and_offset_from_geometry():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_structure(show=False)
    ax = fig.axes[0]

    node_labels = [t for t in ax.texts if getattr(t, "_anastruct_plus_kind", None) == "node"]
    element_labels = [t for t in ax.texts if getattr(t, "_anastruct_plus_kind", None) == "element"]

    assert node_labels
    assert element_labels
    assert all(t.get_color() == "tab:blue" for t in node_labels)
    assert all(t.get_color() == "tab:green" for t in element_labels)
    assert all(t.get_bbox_patch() is not None for t in node_labels + element_labels)
    assert all(t.get_fontweight() == "bold" for t in node_labels + element_labels)
    assert all(hasattr(t, "xy") for t in node_labels + element_labels)
    assert all(t.get_position() != (0, 0) for t in node_labels + element_labels)
```

The fake structure fixture will also be extended to emit node labels `1` and `2`, matching the real anaStruct reference image.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `pytest -q tests/test_axis_semantics.py -k structure_ids`

Expected: FAIL because v0.2.3 does not classify/rebuild native node/element labels.

- [ ] **Step 3: Implement geometry-aware placement**

Implement in `axis_semantics.py`:

```python
def _node_label_offset(self, node):
    cx, cy = self._model_centroid()
    dx = float(node.vertex.x) - cx
    dy = float(node.vertex.y) - cy
    norm = max((dx * dx + dy * dy) ** 0.5, 1e-12)
    if norm <= 1e-12:
        return (8.0, 10.0)
    return (10.0 * dx / norm, 10.0 * dy / norm + 8.0)


def _element_label_offset(self, element):
    x1, y1 = element.vertex_1.x, element.vertex_1.y
    x2, y2 = element.vertex_2.x, element.vertex_2.y
    tx, ty = x2 - x1, y2 - y1
    norm = max((tx * tx + ty * ty) ** 0.5, 1e-12)
    nx, ny = -ty / norm, tx / norm
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    cx, cy = self._model_centroid()
    if nx * (mx - cx) + ny * (my - cy) < 0:
        nx, ny = -nx, -ny
    return (12.0 * nx, 12.0 * ny - 8.0 if abs(ny) < 0.25 else 12.0 * ny)
```

`_style_structure_ids(fig)` must classify native numeric labels by proximity to node coordinates and element midpoints, remove the native label, and recreate it with `ax.annotate(...)`, `tab:blue`/`tab:green`, bold font, and a white semi-opaque bbox. Set `annotation._anastruct_plus_kind` to `node` or `element` for deterministic regression tests.

- [ ] **Step 4: Run the focused structure tests**

Run: `pytest -q tests/test_axis_semantics.py -k 'structure_ids or horizontal_result'`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add anastruct_plus/axis_semantics.py tests/test_axis_semantics.py
git commit -m "fix: separate structure id labels"
```

---

### Task 2: Add safe visual margins to result figures

**Files:**
- Modify: `anastruct_plus/axis_semantics.py`
- Test: `tests/test_axis_semantics.py`

**Interfaces:**
- Consumes: Matplotlib axis limits after the base anaStruct Plus `_tighten_axes()` call.
- Produces: `_add_visual_breathing_room(fig, x_fraction=0.04, y_fraction=0.08) -> None` and `_apply_outer_layout(fig) -> None`.

- [ ] **Step 1: Write failing margin tests**

```python
def test_result_plots_keep_extra_space_around_geometry():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_bending_moment(show=False)
    xmin, xmax = fig.axes[0].get_xlim()
    assert xmin < -0.35
    assert xmax > 4.35


def test_result_axes_keep_nonzero_vertical_headroom():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_shear_force(show=False)
    ymin, ymax = fig.axes[0].get_ylim()
    data_y = [y for line in fig.axes[0].lines for y in line.get_ydata()]
    assert ymin < min(data_y)
    assert ymax > max(data_y)
```

- [ ] **Step 2: Run focused tests and verify failure**

Run: `pytest -q tests/test_axis_semantics.py -k 'extra_space or headroom'`

Expected: FAIL against v0.2.3/v0.2.2 tight limits.

- [ ] **Step 3: Implement margin expansion after axis semantics**

```python
def _add_visual_breathing_room(self, fig, x_fraction=0.04, y_fraction=0.08):
    if not fig.axes:
        return
    ax = fig.axes[0]
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    dx = max(xmax - xmin, 1e-9)
    dy = max(ymax - ymin, 1e-9)
    ax.set_xlim(xmin - x_fraction * dx, xmax + x_fraction * dx)
    ax.set_ylim(ymin - y_fraction * dy, ymax + y_fraction * dy)


def _apply_outer_layout(self, fig):
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.18, top=0.86)
```

Call both from the public `_finish()` after `_style_result_axes(fig)` and before display. For `show_structure()`, use a slightly smaller x expansion and larger y expansion after ID labels are positioned, then use `left=0.07, right=0.97, bottom=0.16, top=0.95`.

- [ ] **Step 4: Run axis/margin regression tests**

Run: `pytest -q tests/test_axis_semantics.py`

Expected: all tests PASS; longitudinal axis labels/ticks remain unchanged from v0.2.3.

- [ ] **Step 5: Commit**

```bash
git add anastruct_plus/axis_semantics.py tests/test_axis_semantics.py
git commit -m "fix: add plot breathing room"
```

---

### Task 3: Anchor `u_max` to the deformed curve with a leader arrow

**Files:**
- Modify: `anastruct_plus/axis_semantics.py`
- Test: `tests/test_axis_semantics.py`

**Interfaces:**
- Consumes: native numeric displacement text positions and line artists already drawn by anaStruct.
- Produces: `_nearest_curve_point(ax, xy) -> tuple[float, float]` and arrow `Annotation` with `_anastruct_plus_kind = "displacement_max"`.

- [ ] **Step 1: Write failing displacement-callout test**

```python
def test_displacement_max_is_nearby_arrow_callout_to_curve():
    ss = SystemElementsPlus(force_unit="tonf", length_unit="m")
    fig = ss.show_displacement(show=False)
    label = next(
        t for t in fig.axes[0].texts
        if getattr(t, "_anastruct_plus_kind", None) == "displacement_max"
    )
    assert label.get_text() == "u_max = 0.003 m"
    assert hasattr(label, "arrow_patch") and label.arrow_patch is not None
    assert hasattr(label, "xy")
    dx, dy = label.get_position()
    assert abs(dx) <= 24
    assert abs(dy) <= 24
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `pytest -q tests/test_axis_semantics.py -k displacement_max_is_nearby`

Expected: FAIL because v0.2.3 puts the value in an axes-corner text box with no leader arrow.

- [ ] **Step 3: Implement nearest-curve anchoring**

```python
def _nearest_curve_point(self, ax, xy):
    x0, y0 = xy
    best = None
    best_d2 = float("inf")
    for line in ax.lines:
        xs = np.asarray(line.get_xdata(), dtype=float)
        ys = np.asarray(line.get_ydata(), dtype=float)
        if xs.size < 3 or ys.size != xs.size:
            continue
        d2 = (xs - x0) ** 2 + (ys - y0) ** 2
        i = int(np.argmin(d2))
        if d2[i] < best_d2:
            best_d2 = float(d2[i])
            best = (float(xs[i]), float(ys[i]))
    return best if best is not None else (float(x0), float(y0))
```

For one native displacement maximum, replace the native numeric text with:

```python
annotation = ax.annotate(
    f"u_max = {raw}{suffix}",
    xy=anchor,
    xytext=(18 if anchor[0] <= x_mid else -18, 18 if anchor[1] <= y_mid else -18),
    textcoords="offset points",
    ha="left" if anchor[0] <= x_mid else "right",
    va="bottom" if anchor[1] <= y_mid else "top",
    fontsize=9,
    bbox={"facecolor": "white", "edgecolor": "0.6", "alpha": 0.9, "pad": 2.0},
    arrowprops={"arrowstyle": "->", "linewidth": 0.8, "shrinkA": 2, "shrinkB": 2},
)
annotation._anastruct_plus_kind = "displacement_max"
```

- [ ] **Step 4: Run displacement and full regression suite**

Run: `pytest -q tests/test_axis_semantics.py tests/test_anastruct_plus.py`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add anastruct_plus/axis_semantics.py tests/test_axis_semantics.py
git commit -m "fix: anchor displacement maximum callout"
```

---

### Task 4: Version, documentation, and CI verification

**Files:**
- Modify: `anastruct_plus/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Produces package version `0.2.4` and automated GitHub Actions verification on pull requests and pushes to `main`.

- [ ] **Step 1: Add the CI workflow**

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e . pytest
      - run: python -m pytest -q
```

- [ ] **Step 2: Bump version and document v0.2.4 behavior**

Set `__version__ = "0.2.4"` in `anastruct_plus/__init__.py` and `version = "0.2.4"` in `pyproject.toml`. Update README bullets to state: distinct node/element IDs, non-overlapping geometry-aware offsets, extra plot margins, and nearby arrow-linked `u_max`.

- [ ] **Step 3: Run final verification**

Run locally or in CI:

```bash
python -m compileall -q anastruct_plus tests
python -m pytest -q
```

Expected: exit code 0 for both commands.

- [ ] **Step 4: Open the pull request and wait for CI**

PR title: `Polish structure labels and displacement callouts`

The PR must remain unmerged until the `tests` workflow is green.

- [ ] **Step 5: Merge only after green CI**

Use squash or merge commit according to repository defaults; then verify `main/pyproject.toml` reports `0.2.4`.
