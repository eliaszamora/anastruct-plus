"""Axis semantics and final plot-layout safeguards for anaStruct Plus."""

from __future__ import annotations

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np

from .system import FigSize, SystemElementsPlus as _BaseSystemElementsPlus


class SystemElementsPlus(_BaseSystemElementsPlus):
    """Public SystemElements with physically honest and legible result plots."""

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _model_axis_mode(self) -> str:
        """Return the single physical longitudinal axis, if the model has one."""
        if not getattr(self, "node_map", None):
            return "general"

        xs = np.asarray([node.vertex.x for node in self.node_map.values()], dtype=float)
        ys = np.asarray([node.vertex.y for node in self.node_map.values()], dtype=float)
        x_span = float(np.ptp(xs)) if xs.size else 0.0
        y_span = float(np.ptp(ys)) if ys.size else 0.0
        tol = 1e-9 * max(1.0, x_span, y_span)

        if x_span > tol and y_span <= tol:
            return "horizontal"
        if y_span > tol and x_span <= tol:
            return "vertical"
        return "general"

    def _model_centroid(self) -> Tuple[float, float]:
        if not getattr(self, "node_map", None):
            return (0.0, 0.0)
        xs = [float(node.vertex.x) for node in self.node_map.values()]
        ys = [float(node.vertex.y) for node in self.node_map.values()]
        return (float(np.mean(xs)), float(np.mean(ys)))

    def _model_span(self) -> float:
        if not getattr(self, "node_map", None):
            return 1.0
        xs = np.asarray([node.vertex.x for node in self.node_map.values()], dtype=float)
        ys = np.asarray([node.vertex.y for node in self.node_map.values()], dtype=float)
        return max(float(np.ptp(xs)), float(np.ptp(ys)), 1.0)

    # ------------------------------------------------------------------
    # Axis semantics and layout
    # ------------------------------------------------------------------

    def _style_result_axes(self, fig) -> None:
        """Hide scaled transverse coordinates that are not physical result values."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        mode = self._model_axis_mode()
        ax.set_xlabel("")
        ax.set_ylabel("")

        if mode == "horizontal":
            if self.length_unit:
                ax.set_xlabel(f"x [{self.length_unit}]")
            ax.set_yticks([])
            ax.yaxis.grid(False)
            if "left" in ax.spines:
                ax.spines["left"].set_visible(False)
        elif mode == "vertical":
            if self.length_unit:
                ax.set_ylabel(f"y [{self.length_unit}]")
            ax.set_xticks([])
            ax.xaxis.grid(False)
            if "bottom" in ax.spines:
                ax.spines["bottom"].set_visible(False)
        else:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)

    @staticmethod
    def _add_visual_breathing_room(
        fig,
        x_fraction: float = 0.04,
        y_fraction: float = 0.08,
    ) -> None:
        """Expand current limits slightly so supports and labels are not flush to edges."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        dx = max(float(xmax - xmin), 1e-9)
        dy = max(float(ymax - ymin), 1e-9)
        ax.set_xlim(xmin - x_fraction * dx, xmax + x_fraction * dx)
        ax.set_ylim(ymin - y_fraction * dy, ymax + y_fraction * dy)

    @staticmethod
    def _apply_outer_layout(fig, structure: bool = False) -> None:
        """Reserve figure-space for titles, axes labels and annotations."""
        if structure:
            fig.subplots_adjust(left=0.07, right=0.97, bottom=0.16, top=0.96)
        else:
            fig.subplots_adjust(left=0.06, right=0.97, bottom=0.18, top=0.86)

    def _finish(self, fig, show: bool):
        """Final public layout step used by all extended plots."""
        is_structure = bool(getattr(self, "_plotting_structure", False))

        if is_structure:
            self._add_visual_breathing_room(fig, x_fraction=0.03, y_fraction=0.10)
            self._apply_outer_layout(fig, structure=True)
        else:
            self._style_result_axes(fig)
            self._add_visual_breathing_room(fig, x_fraction=0.04, y_fraction=0.08)
            self._apply_outer_layout(fig, structure=False)

        if show:
            plt.show()
            return None
        return fig

    # ------------------------------------------------------------------
    # Structure labels
    # ------------------------------------------------------------------

    def _node_label_offset(self, node) -> Tuple[float, float]:
        """Place a node ID outward from the model centroid in screen-space points."""
        cx, cy = self._model_centroid()
        dx = float(node.vertex.x) - cx
        dy = float(node.vertex.y) - cy
        norm = float(np.hypot(dx, dy))

        if norm <= 1e-12:
            return (8.0, 10.0)

        return (10.0 * dx / norm, 8.0 + 8.0 * dy / norm)

    def _element_label_offset(self, element) -> Tuple[float, float]:
        """Place an element ID normal to the member and away from busy geometry."""
        mode = self._model_axis_mode()
        if mode == "horizontal":
            # Distributed-load arrows normally occupy the upper side of a beam.
            return (0.0, -14.0)
        if mode == "vertical":
            return (14.0, 0.0)

        x1 = float(element.vertex_1.x)
        y1 = float(element.vertex_1.y)
        x2 = float(element.vertex_2.x)
        y2 = float(element.vertex_2.y)
        tx = x2 - x1
        ty = y2 - y1
        norm = float(np.hypot(tx, ty))
        if norm <= 1e-12:
            return (0.0, -12.0)

        nx = -ty / norm
        ny = tx / norm
        mx = 0.5 * (x1 + x2)
        my = 0.5 * (y1 + y2)
        cx, cy = self._model_centroid()

        if nx * (mx - cx) + ny * (my - cy) < 0:
            nx, ny = -nx, -ny

        return (12.0 * nx, 12.0 * ny)

    @staticmethod
    def _text_alignment(offset: Tuple[float, float]) -> Tuple[str, str]:
        dx, dy = offset
        if dx > 2:
            ha = "left"
        elif dx < -2:
            ha = "right"
        else:
            ha = "center"

        if dy > 2:
            va = "bottom"
        elif dy < -2:
            va = "top"
        else:
            va = "center"
        return ha, va

    def _classify_structure_id(self, text) -> tuple[str, object, tuple[float, float]] | None:
        """Match a native numeric text artist to the nearest node or element anchor."""
        raw = text.get_text().strip()
        try:
            label_id = int(raw)
        except (TypeError, ValueError):
            return None
        if raw != str(label_id):
            return None

        px, py = map(float, text.get_position())
        candidates = []

        node = getattr(self, "node_map", {}).get(label_id)
        if node is not None:
            anchor = (float(node.vertex.x), float(node.vertex.y))
            distance = float(np.hypot(px - anchor[0], py - anchor[1]))
            candidates.append((distance, "node", node, anchor))

        element = getattr(self, "element_map", {}).get(label_id)
        if element is not None:
            anchor = (
                0.5 * (float(element.vertex_1.x) + float(element.vertex_2.x)),
                0.5 * (float(element.vertex_1.y) + float(element.vertex_2.y)),
            )
            distance = float(np.hypot(px - anchor[0], py - anchor[1]))
            candidates.append((distance, "element", element, anchor))

        if not candidates:
            return None

        distance, kind, obj, anchor = min(candidates, key=lambda item: item[0])
        if distance > 0.35 * self._model_span():
            return None
        return kind, obj, anchor

    def _style_structure_ids(self, fig) -> None:
        """Rebuild native node/element IDs with distinct colors and safe offsets."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        replacements = []

        for text in list(ax.texts):
            classified = self._classify_structure_id(text)
            if classified is None:
                continue
            kind, obj, anchor = classified
            replacements.append((text, kind, obj, anchor))

        for text, kind, obj, anchor in replacements:
            raw = text.get_text().strip()
            fontsize = text.get_fontsize()
            text.remove()

            if kind == "node":
                color = "tab:blue"
                offset = self._node_label_offset(obj)
            else:
                color = "tab:green"
                offset = self._element_label_offset(obj)

            ha, va = self._text_alignment(offset)
            annotation = ax.annotate(
                raw,
                xy=anchor,
                xytext=offset,
                textcoords="offset points",
                ha=ha,
                va=va,
                fontsize=fontsize,
                fontweight="bold",
                color=color,
                zorder=30,
                clip_on=False,
                bbox={
                    "boxstyle": "round,pad=0.18",
                    "facecolor": "white",
                    "edgecolor": color,
                    "linewidth": 0.8,
                    "alpha": 0.9,
                },
            )
            annotation._anastruct_plus_kind = kind

    def show_structure(
        self,
        verbosity: int = 0,
        scale: float = 1.0,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        supports: bool = True,
        values_only: bool = False,
        annotations: bool = False,
    ):
        previous = getattr(self, "_plotting_structure", False)
        self._plotting_structure = True
        try:
            if values_only:
                return super().show_structure(
                    verbosity=verbosity,
                    scale=scale,
                    offset=offset,
                    figsize=figsize,
                    show=show,
                    supports=supports,
                    values_only=True,
                    annotations=annotations,
                )

            # Force show=False so labels can be restyled before the figure is displayed.
            fig = super().show_structure(
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=figsize,
                show=False,
                supports=supports,
                values_only=False,
                annotations=annotations,
            )
            if verbosity == 0:
                self._style_structure_ids(fig)

            if show:
                plt.show()
                return None
            return fig
        finally:
            self._plotting_structure = previous

    # ------------------------------------------------------------------
    # Displacement callout
    # ------------------------------------------------------------------

    @staticmethod
    def _nearest_curve_point(ax, xy: Tuple[float, float]) -> Tuple[float, float]:
        """Return the plotted curve point nearest a native displacement label."""
        x0, y0 = map(float, xy)
        best = None
        best_d2 = float("inf")

        for line in ax.lines:
            xs = np.asarray(line.get_xdata(), dtype=float)
            ys = np.asarray(line.get_ydata(), dtype=float)
            if xs.size < 3 or ys.size != xs.size:
                continue

            finite = np.isfinite(xs) & np.isfinite(ys)
            if not np.any(finite):
                continue
            xs = xs[finite]
            ys = ys[finite]
            d2 = (xs - x0) ** 2 + (ys - y0) ** 2
            i = int(np.argmin(d2))
            if float(d2[i]) < best_d2:
                best_d2 = float(d2[i])
                best = (float(xs[i]), float(ys[i]))

        return best if best is not None else (x0, y0)

    def _label_displacement_values(self, fig) -> None:
        """Replace native displacement numbers by nearby leader-arrow callouts."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        suffix = f" {self.displacement_unit}" if self.displacement_unit else ""
        native = []

        for text in list(ax.texts):
            raw = text.get_text().strip()
            try:
                float(raw)
            except (TypeError, ValueError):
                continue
            native.append((raw, tuple(map(float, text.get_position()))))
            text.remove()

        if not native:
            return

        # Keep the first location for each unique native value.
        unique = []
        seen = set()
        for raw, position in native:
            if raw in seen:
                continue
            seen.add(raw)
            unique.append((raw, position))

        cx, cy = self._model_centroid()

        for index, (raw, native_position) in enumerate(unique):
            anchor = self._nearest_curve_point(ax, native_position)
            dx = 18 if anchor[0] <= cx else -18
            dy = 18 if anchor[1] <= cy else -18
            ha = "left" if dx > 0 else "right"
            va = "bottom" if dy > 0 else "top"
            label = (
                f"u_max = {raw}{suffix}"
                if len(unique) == 1
                else f"u{index + 1} = {raw}{suffix}"
            )

            annotation = ax.annotate(
                label,
                xy=anchor,
                xytext=(dx, dy),
                textcoords="offset points",
                ha=ha,
                va=va,
                fontsize=9,
                zorder=30,
                annotation_clip=False,
                bbox={
                    "boxstyle": "round,pad=0.20",
                    "facecolor": "white",
                    "edgecolor": "0.60",
                    "linewidth": 0.7,
                    "alpha": 0.92,
                },
                arrowprops={
                    "arrowstyle": "->",
                    "linewidth": 0.8,
                    "color": "0.35",
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
            )
            annotation._anastruct_plus_kind = (
                "displacement_max" if len(unique) == 1 else "displacement_value"
            )


SystemElements = SystemElementsPlus
