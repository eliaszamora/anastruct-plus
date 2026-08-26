"""Small plotting extension for anaStruct.

The structural analysis remains entirely in anaStruct. This module only improves
plot presentation: compact automatic figure sizes, unit labels, and relevant
values (element ends + global max/min for each element).
"""

from __future__ import annotations

from typing import Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from anastruct import SystemElements


FigSize = Optional[Union[Tuple[float, float], str]]


class SystemElementsPlus(SystemElements):
    """anaStruct ``SystemElements`` with improved result plots.

    All original anaStruct modelling and analysis methods are inherited unchanged.

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

        if self.distributed_load_unit:
            for text in ax.texts:
                label = text.get_text()
                if label.startswith("q=") and self.distributed_load_unit not in label:
                    text.set_text(f"{label} {self.distributed_load_unit}")

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
        return self._finish(fig, show)


SystemElements = SystemElementsPlus
