"""Lightweight plotting extensions for anaStruct.

anaStruct remains responsible for the structural analysis. This module only adds
compact plotting, visual units, clearer annotations, and tighter framing.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from anastruct import SystemElements


FigSize = Optional[Union[Tuple[float, float], str]]


class SystemElementsPlus(SystemElements):
    """anaStruct ``SystemElements`` with improved result plots.

    All modelling and analysis methods are inherited unchanged from anaStruct.

    Parameters added by this extension:
        force_unit: Display unit for forces, e.g. ``"tonf"`` or ``"kN"``.
        length_unit: Display unit for lengths, e.g. ``"m"`` or ``"mm"``.
        auto_figsize: If True, plots adapt their aspect ratio to the model geometry.
    """

    def __init__(
        self,
        *args,
        force_unit: str = "",
        length_unit: str = "",
        auto_figsize: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.force_unit = force_unit
        self.length_unit = length_unit
        self.auto_figsize = auto_figsize

    @property
    def distributed_load_unit(self) -> str:
        if self.force_unit and self.length_unit:
            return f"{self.force_unit}/{self.length_unit}"
        return ""

    @property
    def moment_unit(self) -> str:
        if self.force_unit and self.length_unit:
            return f"{self.force_unit}·{self.length_unit}"
        return ""

    @property
    def displacement_unit(self) -> str:
        return self.length_unit

    def _auto_figsize(self) -> Tuple[float, float]:
        """Choose a compact figure size from the model aspect ratio."""
        if not getattr(self, "node_map", None):
            return (9.0, 4.0)

        xs = [node.vertex.x for node in self.node_map.values()]
        ys = [node.vertex.y for node in self.node_map.values()]
        x_span = max(xs) - min(xs)
        y_span = max(ys) - min(ys)

        if x_span <= 1e-12 and y_span <= 1e-12:
            return (7.0, 4.0)
        if x_span <= 1e-12:
            return (5.5, 8.0)

        ratio = y_span / x_span
        width = 10.0 if ratio <= 1.2 else 7.0
        height = max(2.8, min(8.0, 2.0 + 7.0 * ratio))
        return (width, height)

    def _resolve_figsize(self, figsize: FigSize) -> Optional[Tuple[float, float]]:
        if figsize == "auto" or (figsize is None and self.auto_figsize):
            return self._auto_figsize()
        if figsize is None:
            return self.figsize
        if isinstance(figsize, tuple):
            return figsize
        raise ValueError("figsize debe ser una tupla, 'auto' o None")

    @staticmethod
    def _finish(fig, show: bool):
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.88)
        if show:
            plt.show()
            return None
        return fig

    @staticmethod
    def _format_value(value: float, decimals: int) -> str:
        if abs(value) < 0.5 * 10 ** (-decimals):
            value = 0.0
        return f"{value:.{decimals}f}"

    @staticmethod
    def _tighten_axes(fig, tighten_y: bool = True, pad_ratio: float = 0.08) -> None:
        """Tighten anaStruct's generous limits around the actual plotted data."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        bounds = np.asarray(ax.dataLim.bounds, dtype=float)
        if not np.all(np.isfinite(bounds)):
            return

        x0, y0, width, height = bounds
        if width > 1e-12:
            x_pad = max(width * pad_ratio, 1e-9)
            ax.set_xlim(x0 - x_pad, x0 + width + x_pad)

        if tighten_y:
            if height > 1e-12:
                y_pad = max(height * 0.30, 1e-9)
                ax.set_ylim(y0 - y_pad, y0 + height + y_pad)
            elif width > 1e-12:
                half_height = max(width * 0.10, 0.25)
                ax.set_ylim(y0 - half_height, y0 + half_height)

    def _collapse_uniform_q_labels(self, fig) -> None:
        """Show one centered value for a uniform q-load instead of two end labels."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        groups = {}
        for text in list(ax.texts):
            label = text.get_text().strip()
            if label.startswith("q="):
                groups.setdefault(label, []).append(text)

        for items in groups.values():
            items.sort(key=lambda text: (text.get_position()[0], text.get_position()[1]))
            for i in range(0, len(items) - 1, 2):
                first, second = items[i], items[i + 1]
                x1, y1 = first.get_position()
                x2, y2 = second.get_position()
                first.set_position(((x1 + x2) / 2, (y1 + y2) / 2))
                second.remove()

        if self.distributed_load_unit:
            for text in ax.texts:
                label = text.get_text().strip()
                if label.startswith("q=") and self.distributed_load_unit not in label:
                    text.set_text(f"{label} {self.distributed_load_unit}")

    def _annotate_relevant_values(
        self,
        fig,
        result_key: str,
        plot_x: np.ndarray,
        plot_y: np.ndarray,
        decimals: int,
    ) -> None:
        """Label both ends and the global max/min of every applicable element."""
        ax = fig.axes[0]
        results = self.get_element_results(verbose=True)
        if isinstance(results, dict):
            results = [results]

        cursor = 0
        plot_attribute = {
            "M": "bending_moment",
            "Q": "shear_force",
            "N": "axial_force",
        }[result_key]

        for result in results:
            values = result.get(result_key)
            element = self.element_map.get(result["id"])
            if element is None:
                continue

            plotted_values = getattr(element, plot_attribute, None)
            plotted_n = len(plotted_values) if plotted_values is not None else 0
            chunk_len = plotted_n + 2
            x_chunk = np.asarray(plot_x[cursor : cursor + chunk_len], dtype=float)
            y_chunk = np.asarray(plot_y[cursor : cursor + chunk_len], dtype=float)
            cursor += chunk_len

            if values is None:
                continue

            values = np.asarray(values, dtype=float)
            n = len(values)
            if len(x_chunk) != chunk_len or n == 0 or plotted_n != n:
                continue

            relevant_indices = {0, n - 1, int(np.argmax(values)), int(np.argmin(values))}

            for i in sorted(relevant_indices):
                x = x_chunk[i + 1]
                y = y_chunk[i + 1]
                value = values[i]
                text = self._format_value(value, decimals)
                dy = 9 if value >= 0 else -11
                va = "bottom" if value >= 0 else "top"
                ax.annotate(
                    text,
                    xy=(x, y),
                    xytext=(0, dy),
                    textcoords="offset points",
                    ha="center",
                    va=va,
                    fontsize=9,
                )

    def _annotate_reactions(self, fig, decimals: int) -> None:
        """Replace anaStruct's generic R=/T= labels with component-aware labels."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        force_suffix = f" {self.force_unit}" if self.force_unit else ""
        moment_suffix = f" {self.moment_unit}" if self.moment_unit else ""

        for node in getattr(self, "reaction_forces", {}).values():
            node_id = getattr(node, "id", "")
            x = node.vertex.x
            y = node.vertex.y
            Fx = float(getattr(node, "Fx", 0.0) or 0.0)
            Fy = float(getattr(node, "Fy", 0.0) or 0.0)
            moment = float(getattr(node, "Tz", getattr(node, "Ty", 0.0)) or 0.0)

            if not np.isclose(Fx, 0.0, rtol=1e-5, atol=1e-9):
                dx = 10 if Fx >= 0 else -10
                ha = "left" if Fx >= 0 else "right"
                ax.annotate(
                    f"R{node_id}x = {self._format_value(Fx, decimals)}{force_suffix}",
                    xy=(x, y),
                    xytext=(dx, 4),
                    textcoords="offset points",
                    ha=ha,
                    va="bottom",
                    fontsize=9,
                )

            if not np.isclose(Fy, 0.0, rtol=1e-5, atol=1e-9):
                dy = 12 if Fy >= 0 else -15
                va = "bottom" if Fy >= 0 else "top"
                ax.annotate(
                    f"R{node_id}y = {self._format_value(Fy, decimals)}{force_suffix}",
                    xy=(x, y),
                    xytext=(4, dy),
                    textcoords="offset points",
                    ha="left",
                    va=va,
                    fontsize=9,
                )

            if not np.isclose(moment, 0.0, rtol=1e-5, atol=1e-9):
                ax.annotate(
                    f"M{node_id} = {self._format_value(moment, decimals)}{moment_suffix}",
                    xy=(x, y),
                    xytext=(8, 18),
                    textcoords="offset points",
                    ha="left",
                    va="bottom",
                    fontsize=9,
                )

    def _label_displacement_values(self, fig) -> None:
        """Identify native numeric displacement annotations and append their unit."""
        if not fig.axes:
            return

        suffix = f" {self.displacement_unit}" if self.displacement_unit else ""
        for text in fig.axes[0].texts:
            raw = text.get_text().strip()
            try:
                float(raw)
            except (TypeError, ValueError):
                continue
            text.set_text(f"u = {raw}{suffix}")

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
        if values_only:
            return super().show_structure(
                verbosity, scale, offset, None, show, supports, True, annotations
            )

        size = self._resolve_figsize(figsize)
        fig = super().show_structure(
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
            supports=supports,
            values_only=False,
            annotations=annotations,
        )
        ax = fig.axes[0]

        if self.length_unit:
            ax.set_xlabel(f"x [{self.length_unit}]")
            ax.set_ylabel(f"y [{self.length_unit}]")

        if verbosity == 0:
            self._collapse_uniform_q_labels(fig)
        self._tighten_axes(fig, tighten_y=True)
        return self._finish(fig, show)

    def show_bending_moment(
        self,
        factor: Optional[float] = None,
        verbosity: int = 0,
        scale: float = 1,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        values_only: bool = False,
        decimals: int = 2,
    ):
        if values_only:
            return super().show_bending_moment(
                factor=factor,
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=None,
                show=show,
                values_only=True,
            )

        size = self._resolve_figsize(figsize)
        fig = super().show_bending_moment(
            factor=factor,
            verbosity=1,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
            values_only=False,
        )

        if verbosity == 0:
            x, y = super().show_bending_moment(factor=factor, values_only=True)
            self._annotate_relevant_values(fig, "M", x, y, decimals)

        title = "Diagrama de momento flector"
        if self.moment_unit:
            title += f" [{self.moment_unit}]"
        fig.axes[0].set_title(title)
        self._tighten_axes(fig, tighten_y=True)
        return self._finish(fig, show)

    def show_shear_force(
        self,
        factor: Optional[float] = None,
        verbosity: int = 0,
        scale: float = 1,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        values_only: bool = False,
        decimals: int = 2,
    ):
        if values_only:
            return super().show_shear_force(
                factor=factor,
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=None,
                show=show,
                values_only=True,
            )

        size = self._resolve_figsize(figsize)
        fig = super().show_shear_force(
            factor=factor,
            verbosity=1,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
            values_only=False,
        )

        if verbosity == 0:
            x, y = super().show_shear_force(factor=factor, values_only=True)
            self._annotate_relevant_values(fig, "Q", x, y, decimals)

        title = "Diagrama de esfuerzo cortante"
        if self.force_unit:
            title += f" [{self.force_unit}]"
        fig.axes[0].set_title(title)
        self._tighten_axes(fig, tighten_y=True)
        return self._finish(fig, show)

    def show_axial_force(
        self,
        factor: Optional[float] = None,
        verbosity: int = 0,
        scale: float = 1,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        values_only: bool = False,
        decimals: int = 2,
    ):
        if values_only:
            return super().show_axial_force(
                factor=factor,
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=None,
                show=show,
                values_only=True,
            )

        size = self._resolve_figsize(figsize)
        fig = super().show_axial_force(
            factor=factor,
            verbosity=1,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
            values_only=False,
        )

        if verbosity == 0:
            x, y = super().show_axial_force(factor=factor, values_only=True)
            self._annotate_relevant_values(fig, "N", x, y, decimals)

        title = "Diagrama de fuerza axial"
        if self.force_unit:
            title += f" [{self.force_unit}]"
        fig.axes[0].set_title(title)
        self._tighten_axes(fig, tighten_y=True)
        return self._finish(fig, show)

    def show_reaction_force(
        self,
        verbosity: int = 0,
        scale: float = 1,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        decimals: int = 2,
    ):
        size = self._resolve_figsize(figsize)
        fig = super().show_reaction_force(
            verbosity=1,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
        )

        fig.axes[0].set_title("Diagrama de reacciones")
        if verbosity == 0:
            self._annotate_reactions(fig, decimals)
        self._tighten_axes(fig, tighten_y=False)
        return self._finish(fig, show)

    def show_displacement(
        self,
        factor: Optional[float] = None,
        verbosity: int = 0,
        scale: float = 1,
        offset: Tuple[float, float] = (0, 0),
        figsize: FigSize = None,
        show: bool = True,
        linear: bool = False,
        values_only: bool = False,
    ):
        if values_only:
            return super().show_displacement(
                factor=factor,
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=None,
                show=show,
                linear=linear,
                values_only=True,
            )

        size = self._resolve_figsize(figsize)
        fig = super().show_displacement(
            factor=factor,
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=size,
            show=False,
            linear=linear,
            values_only=False,
        )

        title = "Diagrama de desplazamientos"
        if self.displacement_unit:
            title += f" [{self.displacement_unit}]"
        fig.axes[0].set_title(title)
        if verbosity == 0:
            self._label_displacement_values(fig)
        self._tighten_axes(fig, tighten_y=True)
        return self._finish(fig, show)


SystemElements = SystemElementsPlus
