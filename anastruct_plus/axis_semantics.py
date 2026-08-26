"""Axis semantics and final plot-layout safeguards for anaStruct Plus."""

from __future__ import annotations

from typing import Tuple

import numpy as np

from .system import FigSize, SystemElementsPlus as _BaseSystemElementsPlus


class SystemElementsPlus(_BaseSystemElementsPlus):
    """Public SystemElements with physically honest axes for scaled result plots."""

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

    def _finish(self, fig, show: bool):
        # All extended result plots pass through _finish. The structure plot is
        # the exception because both x and y are genuine geometric coordinates.
        if not getattr(self, "_plotting_structure", False):
            self._style_result_axes(fig)
        return super()._finish(fig, show)

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
            return super().show_structure(
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=figsize,
                show=show,
                supports=supports,
                values_only=values_only,
                annotations=annotations,
            )
        finally:
            self._plotting_structure = previous

    def _label_displacement_values(self, fig) -> None:
        """Move displacement values into a compact box independent of the curve."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        suffix = f" {self.displacement_unit}" if self.displacement_unit else ""
        numeric = []
        native_positions = []

        for text in list(ax.texts):
            raw = text.get_text().strip()
            try:
                float(raw)
            except (TypeError, ValueError):
                continue
            numeric.append(raw)
            native_positions.append(text.get_position())
            text.remove()

        if not numeric:
            return

        unique = list(dict.fromkeys(numeric))
        if len(unique) == 1:
            label = f"u_max = {unique[0]}{suffix}"
        else:
            label = "\n".join(
                f"u{i + 1} = {value}{suffix}" for i, value in enumerate(unique)
            )

        node_ys = [node.vertex.y for node in getattr(self, "node_map", {}).values()]
        reference_y = float(np.mean(node_ys)) if node_ys else 0.0
        native_y = float(np.mean([pos[1] for pos in native_positions]))
        box_y, va = (0.06, "bottom") if native_y <= reference_y else (0.94, "top")

        ax.text(
            0.02,
            box_y,
            label,
            transform=ax.transAxes,
            ha="left",
            va=va,
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 2.0},
        )


SystemElements = SystemElementsPlus
