import click

from bitsheets.loader import get_scores_pokemon_rby
from bitsheets.player import Player


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
    "--track",
    help="Which track to play",
    required=False,
    default="route_01",
    type=str,
)
@click.option(
    "--fs",
    help="Sampling rate",
    required=False,
    default=44100,
    type=int,
)
def main(rom_pth, ptrs_pth, track, fs):  # noqa: D103
    scores = get_scores_pokemon_rby(rom_pth, ptrs_pth, track)

    player = Player(fs)

    waves = player.get_waves(scores)

    player.play_wave(sum(waves))
    player.wait_done()


if __name__ == "__main__":
    main()
