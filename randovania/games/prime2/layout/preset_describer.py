from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.games.prime2.layout.beam_configuration import BeamAmmoConfiguration, BeamConfiguration
from randovania.games.prime2.layout.echoes_configuration import (
    EchoesConfiguration,
    LayoutSkyTempleKeyMode,
)
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples
    from randovania.layout.base.base_configuration import BaseConfiguration


def create_beam_configuration_description(
    beams: BeamConfiguration,
) -> list[dict[str, bool]]:
    beam_names = ["Power", "Dark", "Light", "Annihilator"]
    translated_beam_names = {
        "Power": "Empowered Light Spear",
        "Dark": "Shadow Laser",
        "Light": "Elucidator",
        "Annihilator": "Beam of Unmaking",
    }
    default_config = BeamConfiguration(
        power=BeamAmmoConfiguration(0, -1, -1, 0, 0, 5, 0),
        dark=BeamAmmoConfiguration(1, 45, -1, 1, 5, 5, 30),
        light=BeamAmmoConfiguration(2, 46, -1, 1, 5, 5, 30),
        annihilator=BeamAmmoConfiguration(3, 46, 45, 1, 5, 5, 30),
    )
    id_to_name = {
        -1: "Nothing",
        43: "Nuclear Weapons Device",
        44: "Rocket",
        45: "Shady Cartridge",
        46: "Brilliant Cartridge",
    }

    result = []

    def format_ammo_cost(b: BeamAmmoConfiguration) -> list[str]:
        if b.ammo_a == b.ammo_b == -1:
            return [""]

        return [
            f"{b.uncharged_cost} (Uncharged)",
            f"{b.charged_cost} (Charged)",
            f"{b.combo_ammo_cost} (Combo)",
        ]

    def format_different_ammo_cost(actual: BeamAmmoConfiguration, default: BeamAmmoConfiguration) -> str:
        a1 = format_ammo_cost(actual)
        d1 = format_ammo_cost(default)

        return "/".join(a for a, d in zip(a1, d1) if a != d)

    def format_ammo_name(b: BeamAmmoConfiguration) -> str:
        if b.ammo_a == b.ammo_b == -1:
            return "no ammo"

        names = [id_to_name[b.ammo_a], id_to_name[b.ammo_b]]
        if "Nothing" in names:
            names.remove("Nothing")

        if all(" Ammo" in n for n in names) and len(names) > 1:
            names[0] = names[0].replace(" Ammo", "")

        return " and ".join(names)

    def format_missile_cost(b: BeamAmmoConfiguration) -> str:
        return f"{b.combo_missile_cost} missiles for combo"

    for name, default_beam, actual_beam in zip(beam_names, default_config.all_beams, beams.all_beams):
        different = []

        ammo_cost = format_different_ammo_cost(actual_beam, default_beam)
        ammo_name = format_ammo_name(actual_beam)
        if ammo_name != format_ammo_name(default_beam) or ammo_cost:
            if ammo_name != "no ammo" and ammo_cost:
                different.append(f"{ammo_cost} {ammo_name}")
            else:
                different.append(ammo_name)

        missile_cost = format_missile_cost(actual_beam)
        if missile_cost != format_missile_cost(default_beam):
            different.append(missile_cost)

        if different:
            description = "{beam} uses {different}".format(
                beam=translated_beam_names[name], different=", ".join(different)
            )
            result.append({description: True})

    return result


class EchoesPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, EchoesConfiguration)
        pickup_database = default_database.pickup_database_for_game(configuration.game)

        template_strings = super().format_params(configuration)
        unified_ammo = configuration.ammo_pickup_configuration.pickups_state[
            pickup_database.ammo_pickups["Ray Toner Expansion"]
        ]

        # Difficulty
        if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (
            6,
            1.2,
        ):
            template_strings["Daredevil Confrontation"].append(
                f"Shadowy Ether exchanges {configuration.varia_suit_damage:.2f} dmg/s to the Variable Armor, "
                f"{configuration.dark_suit_damage:.2f} dmg/s upon the Shadows Wardrobe"
            )

        if configuration.energy_per_tank != 100:
            template_strings["Daredevil Confrontation"].append(
                f"{configuration.energy_per_tank} vitality units for each Power Reservoir"
            )

        if configuration.safe_zone.heal_per_second != 1:
            template_strings["Daredevil Confrontation"].append(
                f"Secure areas rejuvenate  {configuration.safe_zone.heal_per_second:.2f} "
                "vitality each tick of the clock"
            )

        extra_message_tree = {
            "Container of Things": [
                {
                    "Fractured ray projectiles": unified_ammo.pickup_count == 0,
                }
            ],
            "Daredevil Confrontation": [
                {"One Horsepower Fashion": configuration.dangerous_energy_tank},
            ],
            "Level Play Dance": [
                {f"Linguistic Portals: {configuration.translator_configuration.description()}": True},
                {
                    f"Floating Metal Boxes of Ascent: {configuration.teleporters.description('elevators')}": (
                        not configuration.teleporters.is_vanilla
                    )
                },
                {"Gateways: Whimsically Chaotic": configuration.portal_rando},
            ],
            "Play Transition": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Rockets needs Launcher": "Rocket",
                        "Nuclear Weapons Devices requires primary essence": "Energy Explosive Amplification",
                    },
                ),
                {
                    "Twist to initiate": configuration.warp_to_start,
                    "Dish Configuration": configuration.menu_mod,
                    "Ultimate gladiators erased": configuration.teleporters.skip_final_bosses,
                    "Freed portal gateways to preserve dimensions": configuration.blue_save_doors,
                    "Ether Reversed": configuration.inverted_mode,
                },
                {"Fresh Teepee": configuration.use_new_patcher},
                *create_beam_configuration_description(configuration.beam_configuration),
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        # Sky Temple Keys
        if configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
            template_strings["Container of Things"].append("New York Keys with every ruler")
        elif configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            template_strings["Container of Things"].append("New York Keys at each warden")
        else:
            template_strings["Container of Things"].append(f"{configuration.sky_temple_keys.num_keys} New York Keys")

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime2.layout import progressive_items

        return progressive_items.tuples()
