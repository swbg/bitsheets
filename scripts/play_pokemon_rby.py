import click
import yaml

from bitsheets.parser import PokemonRBYParser
from bitsheets.player import Player


@click.command()
@click.option(
    "--rom_pth",
    help="Path to rom file.",
    required=True,
    type=click.Path(),
)
@click.option(
    "--ptrs_pth",
    help="Path to pointers file.",
    required=True,
    type=click.Path(),
)
@click.option(
    "--fs",
    help="Path to rom file.",
    required=False,
    default=44100,
    type=int,
)
def main(rom_pth, ptrs_pth, fs):  # noqa: D103
    with open(rom_pth, "rb") as f:
        rom = f.read()

    with open(ptrs_pth, "r") as f:
        music_ptrs = yaml.safe_load(f)

    parser = PokemonRBYParser(rom)
    player = Player(fs)

    music = "route_01"

    scores = [
        parser.parse_from_pointer(ptr=ptr, ptr_offset=music_ptrs[music]["ptr_offset"])
        for ptr in music_ptrs[music]["channels"]
    ]

    waves = [player.get_wave(score) for score in scores]
    player.play_wave(sum(waves))
    player.wait_done()


if __name__ == "__main__":
    main()
