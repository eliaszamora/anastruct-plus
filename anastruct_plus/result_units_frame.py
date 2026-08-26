"""Final result-label units and plot-frame safeguards for anaStruct Plus."""

from __future__ import annotations

import numpy as np

from .axis_semantics import SystemElementsPlus as _AxisSystemElementsPlus


class SystemElementsPlus(_AxisSystemElementsPlus):
    """Public SystemElements with complete plot frames and unit-bearing values."""

    def _style_result_axes(self, fig) -> None:
        """Keep non-physical transverse ticks hidden without removing the plot frame."""
        super()._style_result_axes(fig)
        if not fig.axes:
            return

        ax = fig.axes[0]
        mode = self._model_axis_mode()

        # v0.2.3 hid these spines together with the non-physical transverse
        # scale. That made the plot look visually clipped. The frame itself is
        # harmless and useful; only the misleading numeric ticks stay hidden.
        if mode == "horizontal" and "left" in ax.spines:
            ax.spines["left"].set_visible(True)
        elif mode == "vertical" and "bottom" in ax.spines:
            ax.spines["bottom"].set_visible(True)

    def _result_unit(self, result_key: str) -> str:
        if result_key == "M":
            return self.moment_unit
        if result_key in {"Q", "N"}:
            return self.force_unit
        return ""

    def _annotate_relevant_values(
        self,
        fig,
        result_key: str,
        plot_x: np.ndarray,
        plot_y: np.ndarray,
        decimals: int,
    ) -> None:
        """Append the configured physical unit to every result-value annotation."""
        if not fig.axes:
            return

        ax = fig.axes[0]
        existing_ids = {id(text) for text in ax.texts}

        super()._annotate_relevant_values(
            fig,
            result_key,
            plot_x,
            plot_y,
            decimals,
        )

        unit = self._result_unit(result_key)
        if not unit:
            return
        suffix = f" {unit}"

        for text in ax.texts:
            if id(text) in existing_ids:
                continue
            label = text.get_text().strip()
            if label and not label.endswith(suffix):
                text.set_text(f"{label}{suffix}")


SystemElements = SystemElementsPlus
