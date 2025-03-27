from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import LocationFormatter
from randovania.game_description.hint import LocationHint
from randovania.game_description.resources.pickup_index import PickupIndex

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.hint import Hint
    from randovania.layout.base.base_configuration import BaseConfiguration


class GuardianFormatter(LocationFormatter):
    _GUARDIAN_NAMES = {
        PickupIndex(43): "Amorbis",
        PickupIndex(79): "Chykka",
        PickupIndex(115): "Quadraxis",
    }
    _TRANSLATED_GUARDIAN_NAMES = {
        PickupIndex(43): "Ambrosia",
        PickupIndex(79): "Chickadee",
        PickupIndex(115): "Quasarexodus",
    }
    configuration: BaseConfiguration

    def __init__(self, colorizer: Callable[[str, bool], str]):
        self.colorizer = colorizer

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        assert isinstance(hint, LocationHint)
        guardian_names = self._GUARDIAN_NAMES
        guardian = guardian_names[hint.target]
        # if self.configuration.april_fools_hints:
        #    return f"{self.colorizer(guardian, with_color)} protecting the gatekeeper {pick_hint.determiner}
        # {pick_hint.pickup_name}."
        # else:
        return f"{self.colorizer(guardian, with_color)} is guarding {pick_hint.determiner}{pick_hint.pickup_name}."
