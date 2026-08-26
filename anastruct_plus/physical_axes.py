"""Physical result-axis calibration for straight beam plots."""

from __future__ import annotations

import re
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from .result_units_frame import SystemElementsPlus as _ResultSystemElementsPlus
from .system import FigSize


class SystemElementsPlus(_ResultSystemElementsPlus):
    """Public SystemElements with calibrated result axes for straight beams."""

    _RESULT_ATTR = {
        "M": "bending_moment",
        "Q": "shear_force",
        "N": "axial_force",
    }

    _RESULT_AXIS_LABEL = {
        "M": "M",
        "Q": "V",
        "N": "N",
    }

    # ------------------------------------------------------------------
    # Structure identifiers
    # ------------------------------------------------------------------

    def _style_structure_ids(self, fig) -> None:
        """Keep the existing styling and make node/element semantics explicit."""
        super()._style_structure_ids(fig)
        if not fig.axes:
            return

        for text in fig.axes[0].texts:
            kind = getattr(text, "_anastruct_plus_kind", "")
            raw = text.get_text().strip()
            if kind == "node" and raw and not raw.startswith("N"):
                text.set_text(f"N{raw}")
            elif kind == "element" and raw and not raw.startswith("E"):
                text.set_text(f"E{raw}")

    # ------------------------------------------------------------------
    # Physical internal-force axes
    # ------------------------------------------------------------------

    def _straight_horizontal_baseline(self) -> Optional[float]:
        if self._model_axis_mode() != "horizontal" or not getattr(self, "node_map", None):
            return None
        ys = np.asarray([node.vertex.y for node in self.node_map.values()], dtype=float)
        if ys.size == 0:
            return None
        return float(np.mean(ys))

    def _result_scale_from_plot(
        self,
        result_key: str,
        plot_y: np.ndarray,
    ) -> Optional[Tuple[float, float, np.ndarray]]:
        """Infer anaStruct's graphical scale from plotted ordinates and real results."""
        baseline = self._straight_horizontal_baseline()
        if baseline is None:
            return None

        results = self.get_element_results(verbose=True)
        if isinstance(results, dict):
            results = [results]

        ratios = []
        physical = []
        cursor = 0
        attribute = self._RESULT_ATTR[result_key]
        plot_y = np.asarray(plot_y, dtype=float)

        for result in results:
            element = self.element_map.get(result.get("id"))
            if element is None:
                continue

            plotted_values = getattr(element, attribute, None)
            plotted_n = len(plotted_values) if plotted_values is not None else 0
            chunk_len = plotted_n + 2
            y_chunk = plot_y[cursor : cursor + chunk_len]
            cursor += chunk_len

            values = result.get(result_key)
            if values is None or plotted_n == 0 or len(y_chunk) != chunk_len:
                continue

            values = np.asarray(values, dtype=float)
            if values.size != plotted_n:
                continue

            y_values = np.asarray(y_chunk[1:-1], dtype=float)
            element_baseline = np.linspace(
                float(element.vertex_1.y),
                float(element.vertex_2.y),
                plotted_n,
            )
            finite = np.isfinite(values) & np.isfinite(y_values)
            nonzero = finite & (np.abs(values) > 1e-12)
            if np.any(nonzero):
                ratios.extend(
                    ((y_values[nonzero] - element_baseline[nonzero]) / values[nonzero]).tolist()
                )
            physical.extend(values[finite].tolist())

        if not ratios or not physical:
            return None

        ratios = np.asarray(ratios, dtype=float)
        ratios = ratios[np.isfinite(ratios) & (np.abs(ratios) > 1e-12)]
        if ratios.size == 0:
            return None

        factor = float(np.median(ratios))
        if not np.isfinite(factor) or abs(factor) <= 1e-12:
            return None

        return baseline, factor, np.asarray(physical, dtype=float)

    @staticmethod
    def _nice_physical_ticks(values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        if values.size == 0:
            return np.asarray([], dtype=float)

        low = min(0.0, float(np.min(values)))
        high = max(0.0, float(np.max(values)))
        if np.isclose(low, high):
            span = max(abs(low), 1.0)
            low -= 0.5 * span
            high += 0.5 * span

        locator = MaxNLocator(nbins=7, steps=[1, 2, 2.5, 5, 10])
        nice = np.asarray(locator.tick_values(low, high), dtype=float)
        tol = 1e-10 * max(1.0, abs(low), abs(high))
        nice = nice[(nice >= low - tol) & (nice <= high + tol)]

        diffs = np.diff(np.sort(nice))
        diffs = diffs[diffs > tol]
        step = float(np.median(diffs)) if diffs.size else max(high - low, 1.0)

        exact = [low, high]
        if low < 0 < high or np.isclose(low, 0.0) or np.isclose(high, 0.0):
            exact.append(0.0)

        kept = []
        for tick in nice:
            if any(
                not np.isclose(tick, edge, atol=tol)
                and abs(tick - edge) < 0.35 * step
                for edge in (low, high)
            ):
                continue
            kept.append(float(tick))

        ticks = np.asarray(kept + exact, dtype=float)
        ticks[np.isclose(ticks, 0.0, atol=tol)] = 0.0
        return np.unique(np.round(ticks, 12))

    @staticmethod
    def _format_tick(value: float) -> str:
        if abs(value) < 5e-13:
            value = 0.0
        return f"{value:.6g}"

    def _apply_physical_axis(
        self,
        fig,
        baseline: float,
        factor: float,
        physical_values: np.ndarray,
        ylabel: str,
    ) -> None:
        if not fig.axes:
            return

        ticks = self._nice_physical_ticks(physical_values)
        if ticks.size == 0:
            return

        positions = baseline + factor * ticks
        order = np.argsort(positions)
        positions = positions[order]
        ticks = ticks[order]

        ax = fig.axes[0]
        ax.set_yticks(positions)
        ax.set_yticklabels([self._format_tick(value) for value in ticks])
        ax.set_ylabel(ylabel)
        ax.yaxis.grid(True, alpha=0.28)
        if "left" in ax.spines:
            ax.spines["left"].set_visible(True)

        ymin = float(np.min(positions))
        ymax = float(np.max(positions))
        span = max(ymax - ymin, abs(factor) * max(float(np.ptp(ticks)), 1e-9), 1e-9)
        pad = 0.18 * span
        ax.set_ylim(ymin - pad, ymax + pad)
        fig.subplots_adjust(left=0.12, right=0.97, bottom=0.18, top=0.86)
        ax._anastruct_plus_physical_y = {
            "baseline": baseline,
            "factor": factor,
            "ylabel": ylabel,
        }

    def _physicalize_internal_force_axis(
        self,
        fig,
        result_key: str,
        plot_y: np.ndarray,
    ) -> None:
        scale = self._result_scale_from_plot(result_key, plot_y)
        if scale is None:
            return

        baseline, factor, values = scale
        unit = self._result_unit(result_key)
        symbol = self._RESULT_AXIS_LABEL[result_key]
        ylabel = f"{symbol} [{unit}]" if unit else symbol
        self._apply_physical_axis(fig, baseline, factor, values, ylabel)

    # ------------------------------------------------------------------
    # Physical displacement axis
    # ------------------------------------------------------------------

    def _physicalize_displacement_axis(self, fig) -> None:
        baseline = self._straight_horizontal_baseline()
        if baseline is None or not fig.axes:
            return

        ratios = []
        signed_values = []
        for text in fig.axes[0].texts:
            kind = getattr(text, "_anastruct_plus_kind", "")
            if kind not in {"displacement_max", "displacement_value"}:
                continue
            match = re.search(r"=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text.get_text())
            if match is None or not hasattr(text, "xy"):
                continue

            magnitude = abs(float(match.group(1)))
            delta = float(text.xy[1]) - baseline
            if magnitude <= 1e-15 or abs(delta) <= 1e-15:
                continue

            signed = float(np.copysign(magnitude, delta))
            ratios.append(abs(delta) / magnitude)
            signed_values.append(signed)

        if not ratios or not signed_values:
            return

        factor = float(np.median(np.asarray(ratios, dtype=float)))
        if not np.isfinite(factor) or factor <= 1e-12:
            return

        values = np.asarray(signed_values + [0.0], dtype=float)
        unit = self.displacement_unit
        ylabel = f"u_y [{unit}]" if unit else "u_y"
        self._apply_physical_axis(fig, baseline, factor, values, ylabel)

    # ------------------------------------------------------------------
    # Public plot wrappers
    # ------------------------------------------------------------------

    @staticmethod
    def _return_plot(fig, show: bool):
        if show:
            plt.show()
            return None
        return fig

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
                figsize=figsize,
                show=show,
                values_only=True,
                decimals=decimals,
            )

        fig = super().show_bending_moment(
            factor=factor,
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=figsize,
            show=False,
            values_only=False,
            decimals=decimals,
        )
        if self._model_axis_mode() == "horizontal":
            _, plot_y = super().show_bending_moment(factor=factor, values_only=True)
            self._physicalize_internal_force_axis(fig, "M", plot_y)
        return self._return_plot(fig, show)

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
                figsize=figsize,
                show=show,
                values_only=True,
                decimals=decimals,
            )

        fig = super().show_shear_force(
            factor=factor,
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=figsize,
            show=False,
            values_only=False,
            decimals=decimals,
        )
        if self._model_axis_mode() == "horizontal":
            _, plot_y = super().show_shear_force(factor=factor, values_only=True)
            self._physicalize_internal_force_axis(fig, "Q", plot_y)
        return self._return_plot(fig, show)

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
                figsize=figsize,
                show=show,
                values_only=True,
                decimals=decimals,
            )

        fig = super().show_axial_force(
            factor=factor,
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=figsize,
            show=False,
            values_only=False,
            decimals=decimals,
        )
        if self._model_axis_mode() == "horizontal":
            _, plot_y = super().show_axial_force(factor=factor, values_only=True)
            self._physicalize_internal_force_axis(fig, "N", plot_y)
        return self._return_plot(fig, show)

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
                figsize=figsize,
                show=show,
                linear=linear,
                values_only=True,
            )

        fig = super().show_displacement(
            factor=factor,
            verbosity=verbosity,
            scale=scale,
            offset=offset,
            figsize=figsize,
            show=False,
            linear=linear,
            values_only=False,
        )
        if self._model_axis_mode() == "horizontal" and verbosity == 0:
            self._physicalize_displacement_axis(fig)
        return self._return_plot(fig, show)


SystemElements = SystemElementsPlus
