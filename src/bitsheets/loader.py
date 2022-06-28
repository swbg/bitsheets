import yaml

from .parser import PokemonRBYParser
from .types import ScoresType


def get_scores_pokemon_rby(rom_pth: str, ptrs_pth: str, music: str) -> ScoresType:
    """
    Load scores from Pokemon RBY rom.

    :param rom_pth: Path to rom file
    :param ptrs_path: Path to pointers file
    :param music: Which track to load
    """
    with open(rom_pth, "rb") as f:
        rom = f.read()

    with open(ptrs_pth, "r") as f:
        music_ptrs = yaml.safe_load(f)

    parser = PokemonRBYParser(rom)

    return [
        parser.parse_from_pointer(ptr=ptr, ptr_offset=music_ptrs[music]["ptr_offset"])
        for ptr in music_ptrs[music]["channels"]
    ]
