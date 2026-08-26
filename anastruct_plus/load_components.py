"""Named distributed-load components built on top of anaStruct's q-load solver."""

from __future__ import annotations

from numbers import Real
from typing import Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

from .physical_axes import SystemElementsPlus as _PhysicalAxesSystemElementsPlus
from .system import FigSize


class SystemElementsPlus(_PhysicalAxesSystemElementsPlus):
    """anaStruct Plus with compact named components for distributed loads.

    Traditional ``q_load(q=...)`` calls retain anaStruct's original replacement
    semantics. Named keyword components, e.g. ``pp=-4, sc=-3``, are stored
    separately and their algebraic resultant is the only q-load sent to the
    anaStruct solver.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.q_load_components = {}

    @staticmethod
    def _single_element_id(element_id) -> int:
        if isinstance(element_id, (int, np.integer)):
            return int(element_id)
        raise ValueError(
            "Las componentes nombradas de q_load requieren un único element_id."
        )

    @staticmethod
    def _component_value(name: str, value) -> float:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(
                f"La componente '{name}' debe ser un valor numérico escalar."
            )
        return float(value)

    @staticmethod
    def _same_setting(left, right) -> bool:
        if left is None or right is None:
            return left is right
        try:
            return bool(np.allclose(left, right))
        except (TypeError, ValueError):
            return left == right

    def q_load(
        self,
        q=None,
        element_id=None,
        direction="element",
        rotation=None,
        q_perp=None,
        **components,
    ) -> None:
        """Apply a traditional q-load or one or more named q components.

        Examples::

            ss.q_load(element_id=1, q=-7)
            ss.q_load(element_id=1, pp=-4, sc=-3)
            ss.q_load(element_id=1, pp=-4)
            ss.q_load(element_id=1, sc=-3)

        Named components are combined algebraically before delegating to
        anaStruct. Mixing ``q=`` and named components in the same call is
        intentionally rejected to keep the input unambiguous.
        """
        if components and q is not None:
            raise ValueError(
                "No mezcles q= con componentes nombradas en la misma llamada a q_load()."
            )

        if not components:
            if q is None:
                raise TypeError("q_load() requiere q= o al menos una componente nombrada.")

            # Preserve native anaStruct behavior exactly for traditional calls.
            ids = (
                [int(element_id)]
                if isinstance(element_id, (int, np.integer))
                else list(element_id)
                if element_id is not None
                else []
            )
            for element in ids:
                self.q_load_components.pop(element, None)
            return super().q_load(
                q=q,
                element_id=element_id,
                direction=direction,
                rotation=rotation,
                q_perp=q_perp,
            )

        if q_perp is not None:
            raise ValueError(
                "q_perp todavía no se admite junto con componentes nombradas."
            )

        element = self._single_element_id(element_id)
        named = {
            name: self._component_value(name, value)
            for name, value in components.items()
        }

        state = self.q_load_components.get(element)
        if state is None:
            state = {
                "components": {},
                "direction": direction,
                "rotation": rotation,
                "q_perp": q_perp,
            }
            self.q_load_components[element] = state
        else:
            if state["direction"] != direction:
                raise ValueError(
                    "Todas las componentes nombradas de un elemento deben usar la misma direction."
                )
            if not self._same_setting(state["rotation"], rotation):
                raise ValueError(
                    "Todas las componentes nombradas de un elemento deben usar la misma rotation."
                )

        # A repeated component name updates that component; distinct names add
        # to the load decomposition. Dict insertion order preserves input order
        # for the structure annotation.
        state["components"].update(named)
        resultant = float(sum(state["components"].values()))

        super().q_load(
            q=resultant,
            element_id=element,
            direction=direction,
            rotation=rotation,
            q_perp=None,
        )

    def remove_loads(self, *args, **kwargs):
        self.q_load_components.clear()
        return super().remove_loads(*args, **kwargs)

    def _format_component_summary(self, element_id: int) -> str:
        state = self.q_load_components[element_id]
        unit = f" {self.distributed_load_unit}" if self.distributed_load_unit else ""
        lines = [
            f"{name} = {abs(value):.1f}{unit}"
            for name, value in state["components"].items()
        ]
        resultant = abs(float(sum(state["components"].values())))
        lines.append(f"Σq = {resultant:.1f}{unit}")
        return "\n".join(lines)

    def _annotate_q_components(self, fig) -> None:
        if not fig.axes or not self.q_load_components:
            return

        ax = fig.axes[0]
        q_labels = [text for text in ax.texts if text.get_text().strip().startswith("q=")]

        for element_id in self.q_load_components:
            element = self.element_map.get(element_id)
            if element is None:
                continue

            x_mid = (float(element.vertex_1.x) + float(element.vertex_2.x)) / 2
            y_mid = (float(element.vertex_1.y) + float(element.vertex_2.y)) / 2
            summary = self._format_component_summary(element_id)

            candidates = []
            for text in q_labels:
                if not text.get_visible():
                    continue
                xy = getattr(text, "xy", None)
                if xy is None:
                    continue
                distance = (float(xy[0]) - x_mid) ** 2 + (float(xy[1]) - y_mid) ** 2
                candidates.append((distance, text))

            if candidates:
                _, label = min(candidates, key=lambda item: item[0])
                label.set_text(summary)
                label.set_ha("center")
                label.set_va("bottom")
                label._anastruct_plus_kind = "q_component_summary"
                q_labels.remove(label)
            else:
                annotation = ax.annotate(
                    summary,
                    xy=(x_mid, y_mid),
                    xytext=(0, 12),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    color="blue",
                    fontsize=9,
                )
                annotation._anastruct_plus_kind = "q_component_summary"

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
                verbosity=verbosity,
                scale=scale,
                offset=offset,
                figsize=figsize,
                show=show,
                supports=supports,
                values_only=True,
                annotations=annotations,
            )

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
            self._annotate_q_components(fig)

        if show:
            plt.show()
            return None
        return fig


SystemElements = SystemElementsPlus
