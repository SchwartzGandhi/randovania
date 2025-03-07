from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime2.exporter.export_params import EchoesGameExportParams
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.games.prime2.gui.dialog.game_export_dialog import EchoesGameExportDialog
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(
    skip_qtbot, tmp_path, mocker, has_output_dir, default_echoes_configuration, options
):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "Echoes Randomizer - MyHash"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "Echoes Randomizer - MyHash"

    with options:
        options.set_per_game_options(
            EchoesPerGameOptions(
                cosmetic_patches=EchoesCosmeticPatches.default(),
                output_directory=output_directory,
            )
        )

    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".iso", ["iso"])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker, default_echoes_configuration, options):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)
    with options:
        options.set_per_game_options(
            EchoesPerGameOptions(
                cosmetic_patches=EchoesCosmeticPatches.default(),
                output_directory=None,
            )
        )

    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Echoes Randomizer - MyHash.iso", ["iso"])
    assert window.output_file_edit.text() == ""


@pytest.mark.parametrize("is_prime_multi", [False, True])
def test_save_options(skip_qtbot, tmp_path, is_prime_multi, default_echoes_configuration, options):
    games = [RandovaniaGame.METROID_PRIME_ECHOES]
    if is_prime_multi:
        games.append(RandovaniaGame.METROID_PRIME)
    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, games)
    window.output_file_edit.setText("somewhere/game.iso")
    if is_prime_multi:
        skip_qtbot.mouseClick(window.prime_models_check, QtCore.Qt.MouseButton.LeftButton)
        window.prime_file_edit.setText("somewhere/prime.iso")

    # Run
    window.save_options()

    # Assert
    assert options.per_game_options(EchoesPerGameOptions).output_directory == Path("somewhere")
    if is_prime_multi:
        assert options.per_game_options(PrimePerGameOptions).input_path == Path("somewhere/prime.iso")
        assert options.per_game_options(EchoesPerGameOptions).use_external_models == {RandovaniaGame.METROID_PRIME}


def test_on_input_file_button(skip_qtbot, tmp_path, mocker, default_echoes_configuration, options):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    mock_discover: MagicMock = mocker.patch(
        "randovania.games.common.prime_family.gui.export_validator.discover_game",
        autospec=True,
        return_value=("G2ME01", "Metroid Prime 2"),
    )
    mock_prompt = mocker.patch(
        "randovania.gui.lib.common_qt_lib.prompt_user_for_vanilla_input_file",
        autospec=True,
        side_effect=[
            None,
            tmp_path.joinpath("some/game.iso"),
            tmp_path.joinpath("existing.iso"),
            tmp_path.joinpath("missing_again.iso"),
        ],
    )

    with options:
        options.set_per_game_options(
            EchoesPerGameOptions(
                cosmetic_patches=EchoesCosmeticPatches.default(),
                input_path=None,
            )
        )

    contents_path = tmp_path.joinpath("internal_copies", "prime2", "contents")
    contents_path.mkdir(parents=True)
    mocker.patch(
        "randovania.interface_common.game_workdir.discover_game",
        side_effect=[
            ("G2M", 1),
            None,
        ],
    )

    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, [])
    assert window.input_file_edit.text() == "(internal game copy)"
    assert not window.input_file_edit.has_error

    # Deletes the internal data
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # User cancelled, stays unchanged
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("some/game.iso"))
    assert window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing.iso"))
    assert not window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing_again.iso"))
    assert window.input_file_edit.has_error

    mock_prompt.assert_has_calls(
        [
            call(window, ["iso"], existing_file=None),
            call(window, ["iso"], existing_file=None),
            call(window, ["iso"], existing_file=None),
            call(window, ["iso"], existing_file=tmp_path.joinpath("existing.iso")),
        ]
    )
    mock_discover.assert_called_once_with(tmp_path.joinpath("existing.iso"))


@pytest.mark.parametrize("is_prime_multi", [False, True])
@pytest.mark.parametrize("use_external_models", [False, True])
def test_get_game_export_params(
    skip_qtbot, tmp_path, is_prime_multi, use_external_models, default_echoes_configuration, options
):
    # Setup
    games = [RandovaniaGame.METROID_PRIME_ECHOES]
    if is_prime_multi:
        games.append(RandovaniaGame.METROID_PRIME)
        prime_path = tmp_path.joinpath("input/prime.iso")
    else:
        prime_path = None

    if use_external_models:
        models = {RandovaniaGame.METROID_PRIME}
    else:
        models = set()

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            EchoesPerGameOptions(
                cosmetic_patches=EchoesCosmeticPatches.default(),
                input_path=tmp_path.joinpath("input/game.iso"),
                output_directory=tmp_path.joinpath("output"),
                use_external_models=models,
            )
        )
        options.set_per_game_options(
            PrimePerGameOptions(
                cosmetic_patches=PrimeCosmeticPatches.default(),
                input_path=prime_path,
            )
        )

    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, games)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == EchoesGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "Echoes Randomizer - MyHash.rdvgame"),
        input_path=tmp_path.joinpath("input/game.iso"),
        output_path=tmp_path.joinpath("output", "Echoes Randomizer - MyHash.iso"),
        contents_files_path=tmp_path.joinpath("internal_copies", "prime2", "contents"),
        backup_files_path=tmp_path.joinpath("internal_copies", "prime2", "vanilla"),
        asset_cache_path=tmp_path.joinpath("internal_copies", "prime2", "prime1_models"),
        prime_path=prime_path,
        use_prime_models=is_prime_multi and use_external_models,
    )


async def test_handle_unable_to_export(
    skip_qtbot, tmp_path: Path, mocker: pytest_mock.MockerFixture, default_echoes_configuration, options
) -> None:
    with options:
        options.set_per_game_options(
            EchoesPerGameOptions(
                cosmetic_patches=EchoesCosmeticPatches.default(),
                output_directory=None,
            )
        )

    tmp_path.joinpath("internal_copies", "prime2").mkdir(parents=True)
    tmp_path.joinpath("internal_copies", "prime2", "example_file.txt").write_text("hey I'm a game")

    mock_message_box = mocker.patch("randovania.gui.lib.async_dialog.message_box", new_callable=AsyncMock)

    window = EchoesGameExportDialog(options, default_echoes_configuration, "MyHash", True, [])

    # Run
    await window.handle_unable_to_export(UnableToExportError("I dunno, something broke"))

    # Assert
    assert not tmp_path.joinpath("internal_copies", "prime2").is_dir()
    mock_message_box.assert_awaited_once_with(
        None,
        QtWidgets.QMessageBox.Icon.Critical,
        "Unable to export",
        "I dunno, something broke",
    )
