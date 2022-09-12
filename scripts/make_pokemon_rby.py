import os
import subprocess

import click
import yaml

from bitsheets.lilypond import dump_scores_lilypond
from bitsheets.loader import get_scores_pokemon_rby
from bitsheets.processing import apply_processing


@click.command()
@click.option(
    "--rom_pth",
    help="Path to rom file",
    required=True,
    type=click.Path(),
)
@click.option(
    "--ptrs_pth",
    help="Path to pointers file",
    required=True,
    type=click.Path(),
)
@click.option(
    "--config_pth",
    help="Path to sheets config file",
    required=True,
    type=click.Path(),
)
@click.option(
    "--track",
    help="Which track to make",
    required=False,
    default="route_01",
    type=str,
)
@click.option(
    "--midi/--no-midi",
    help="Whether to create MIDI output",
    is_flag=True,
    default=False,
    type=bool,
)
@click.option(
    "--lily/--no-lily",
    help="Whether to run lilypond",
    is_flag=True,
    default=True,
    type=bool,
)
@click.option(
    "--out_pth",
    help="Output path",
    required=False,
    default=".",
    type=click.Path(),
)
def main(rom_pth, ptrs_pth, track, config_pth, midi, lily, out_pth):  # noqa: D103
    scores = get_scores_pokemon_rby(rom_pth, ptrs_pth, track)

    with open(config_pth, "r") as f:
        sheets_config = yaml.safe_load(f)[track]

    # Preprocess scores
    scores = apply_processing(scores, sheets_config)

    lily_pth = os.path.join(out_pth, track + ".lily")

    dump_scores_lilypond(
        scores,
        lily_pth,
        header_args={
            "title": sheets_config["title"],
            "composer": "Junichi Masuda",
            "dedication": "Pokémon Red&Blue",
        },
        sheets_config=sheets_config,
        midi=midi,
    )

    if lily:
        return subprocess.call(
            ["lilypond", "-o", os.path.join(out_pth, track), lily_pth]
        )


if __name__ == "__main__":
    main()
