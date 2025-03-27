from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.prime2.gui.generated.preset_echoes_hints_ui import Ui_PresetEchoesHints
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.hints_tab import PresetHints

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["april_fools_hints"]


class PresetEchoesHints(PresetHints, Ui_PresetEchoesHints):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)

        self.chaos_box = QtWidgets.QGroupBox()
        self.chaos_box.setTitle("Chaos Hints")
        self.chaos_layout = QtWidgets.QVBoxLayout(self.chaos_box)

        extra_widgets: list[tuple[type[QtWidgets.QCheckBox | QtWidgets.QLabel], str, str]] = [
            (QtWidgets.QCheckBox, "april_fools_hints_check", "April Fools Hints"),
            (
                QtWidgets.QLabel,
                "april_fools_hints_label",
                (
                    "Replaces all hints with text generated in google translate. "
                    "This will severely impact the readability of hints."
                ),
            ),
        ]

        # Add each widget
        for widget_type, attr_name, desc in extra_widgets:
            setattr(self, attr_name, widget_type())
            widget = getattr(self, attr_name)
            widget.setText(desc)
            if widget_type == QtWidgets.QLabel:
                assert isinstance(widget, QtWidgets.QLabel)
                widget.setWordWrap(True)

            self.chaos_layout.addWidget(widget)

        # Add the group box
        self.scroll_area_layout.insertWidget(0, self.chaos_box)

        # Checkbox Signals
        for f in _CHECKBOX_FIELDS:
            self._add_checkbox_persist_option(getattr(self, f"{f}_check"), f)

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        super().on_preset_changed(preset)
        config = preset.configuration
        assert isinstance(config, EchoesConfiguration)
        for f in _CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
