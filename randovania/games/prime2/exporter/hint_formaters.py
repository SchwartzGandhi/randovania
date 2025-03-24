from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import LocationFormatter
from randovania.game_description.hint import LocationHint
from randovania.game_description.resources.pickup_index import PickupIndex

#This should eventually be determined from hints preset value in some way
preset_fools = False

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.hint import Hint


class GuardianFormatter(LocationFormatter):
    if preset_fools == True:
        _GUARDIAN_NAMES = {
            PickupIndex(43): "Ambrosia",
            PickupIndex(79): "Chickadee",
            PickupIndex(115): "Quasarexodus",
        }
    else:
        _GUARDIAN_NAMES = {
            PickupIndex(43): "Amorbis",
            PickupIndex(79): "Chykka",
            PickupIndex(115): "Quadraxis",
        }

    def __init__(self, colorizer: Callable[[str, bool], str]):
        self.colorizer = colorizer

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        assert isinstance(hint, LocationHint)
        guardian = self._GUARDIAN_NAMES[hint.target]
        if preset_fools == True:
            return f"{self.colorizer(guardian, with_color)} protecting the gatekeeper {pick_hint.determiner}{pick_hint.pickup_name}."
        else: 
            return f"{self.colorizer(guardian, with_color)} is guarding {pick_hint.determiner}{pick_hint.pickup_name}."
