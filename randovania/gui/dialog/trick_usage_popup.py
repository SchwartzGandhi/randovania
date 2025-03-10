from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.generated.trick_usage_popup_ui import Ui_TrickUsagePopup
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.data_editor_links import data_editor_href, on_click_data_editor_link
from randovania.layout import filtered_database
from randovania.layout.base.trick_level import LayoutTrickLevel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from PySide6.QtWidgets import QWidget

    from randovania.game_description.db.area import Area
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.layout.preset import Preset


def _area_requirement_sets(
    area: Area,
    context: NodeContext,
) -> Iterator[RequirementSet]:
    """
    Checks the area RequirementSet in the given Area uses the given trick at the given level.
    :param area:
    :param database:
    :return:
    """

    for node in area.nodes:
        if isinstance(node, DockNode):
            yield node.default_dock_weakness.requirement.as_set(context)

        for req in area.connections[node].values():
            yield req.as_set(context)


def _check_used_tricks(area: Area, trick_resources: ResourceCollection, context: NodeContext) -> list[str]:
    result = set()

    for s in _area_requirement_sets(area, context):
        for alternative in s.alternatives:
            tricks: dict[TrickResourceInfo, ResourceRequirement] = {
                req.resource: req for req in alternative.values() if req.resource.resource_type == ResourceType.TRICK
            }
            if tricks and all(trick_resources[trick] >= tricks[trick].amount for trick in tricks):
                line = [
                    f"{trick.long_name} ({LayoutTrickLevel.from_number(req.amount).long_name})"
                    for trick, req in tricks.items()
                ]
                result.add(" and ".join(sorted(line)))

    return sorted(result)


class TrickUsagePopup(QtWidgets.QDialog, Ui_TrickUsagePopup):
    def __init__(
        self,
        parent: QWidget,
        window_manager: WindowManager,
        preset: Preset,
    ):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._window_manager = window_manager
        self._game_description = filtered_database.game_description_for_layout(preset.configuration)
        database = self._game_description.resource_database

        trick_level = preset.configuration.trick_level
        if trick_level.minimal_logic:
            trick_usage_description = "Minimal Logic"
        else:
            trick_usage_description = ", ".join(
                sorted(
                    f"{trick.long_name} ({trick_level.level_for_trick(trick).long_name})"
                    for trick in database.trick
                    if trick_level.has_specific_level_for_trick(trick)
                )
            )

        # setup
        self.area_list_label.linkActivated.connect(
            on_click_data_editor_link(
                self._window_manager,
                self._game_description.game,
            )
        )
        self.setWindowTitle(f"{self.windowTitle()} for preset {preset.name}")
        self.title_label.setText(self.title_label.text().format(trick_levels=trick_usage_description))

        # connect
        self.button_box.accepted.connect(self.button_box_close)
        self.button_box.rejected.connect(self.button_box_close)

        if trick_level.minimal_logic:
            return

        # Update
        bootstrap = self._game_description.game.generator.bootstrap
        trick_resources = ResourceCollection.from_resource_gain(
            database, bootstrap.trick_resources_for_configuration(trick_level, database)
        )
        context = NodeContext(None, trick_resources, database, self._game_description.region_list)

        lines = []

        for region in sorted(self._game_description.region_list.regions, key=lambda it: it.name):
            for area in sorted(region.areas, key=lambda it: it.name):
                used_tricks = _check_used_tricks(area, trick_resources, context)
                if used_tricks:
                    lines.append(data_editor_href(region, area) + f"<br />{'<br />'.join(used_tricks)}</p>")

        self.area_list_label.setText("".join(lines))

    def button_box_close(self):
        self.reject()
