import logging

from .const import NOTES

_logger = logging.getLogger(__name__)


class PokemonRBYParser:
    def __init__(self, rom: bytes):
        """
        Class for parsing Pokemon RBY roms.

        :param rom: Rom
        """
        self.rom = rom

    def parse_from_pointer(self, ptr: int, ptr_offset: int):
        """
        Start parsing music from indicated pointer.

        :param ptr: Start pointer
        :param ptr_offset: Bank-specific pointer offset
        """
        score = []

        c_ptr = ptr_offset + ptr
        ret_ptr = None
        skip_next = 0
        octave_exp = None
        speed_multiplier = 1
        followed_ptrs = set()

        while True:
            byt = self.rom[c_ptr]
            prev_c_ptr = c_ptr  # for debugging
            c_ptr += 1
            cmd = byt >> 4  # upper 4 bits
            arg = byt % 2**4  # lower 4 bits

            if skip_next > 0:
                # Skip line (ignored argument)
                skip_next -= 1
                debug_msg = "Skip"
            elif byt == 0xDC:
                # Velocity?
                skip_next = 1
                speed_multiplier = 1  # for 0xd? in next byte
                debug_msg = "Velocity"
            elif byt == 0xEC:
                # Instrument selection 0xec 0x??
                skip_next = 1
                debug_msg = "Instrument"
            elif byt in [0xF8]:
                # Not sure what this is
                skip_next = 0
                debug_msg = "Unknown skip 0"
            elif byt in [0xD4, 0xDD, 0xEE, 0xF0, 0xFC]:
                # Not sure what this is
                skip_next = 1
                debug_msg = "Unknown skip 1"
            elif byt in [0xED, 0xEA]:
                # Not sure what this is
                skip_next = 2
                debug_msg = "Unknown skip 2"
            elif byt in [0xEB]:
                # Not sure what this is
                skip_next = 3
                debug_msg = "Unknown skip 3"
            elif byt == 0xD6:
                # Play at 2x speed
                skip_next = 1
                speed_multiplier = 2
                debug_msg = "Speed x2"
            elif byt == 0xD8:
                # Play at 1.5x speed
                skip_next = 1
                speed_multiplier = 1.5
                debug_msg = "Speed x1.5"
            elif byt == 0xFE:
                # Jump once to pointer in byte 3 and 4 if byte 2 > 0
                if self.rom[c_ptr] and c_ptr not in followed_ptrs:
                    followed_ptrs.add(c_ptr)
                    ret_ptr = c_ptr + 3
                    c_ptr = (
                        ptr_offset + (self.rom[c_ptr + 2] << 8) + self.rom[c_ptr + 1]
                    )
                elif ret_ptr is not None:
                    c_ptr = ret_ptr
                    ret_ptr = None
                else:
                    _logger.info(f"Encountered end {hex(byt)}")
                    break
                debug_msg = f"Jump to {hex(c_ptr)} (3 bytes)"
            elif byt == 0xFD:
                # Jump to pointer in byte 2 and 3
                ret_ptr = c_ptr + 2
                c_ptr = ptr_offset + (self.rom[c_ptr + 1] << 8) + self.rom[c_ptr]
                debug_msg = f"Jump to {hex(c_ptr)} (2 bytes)"
            elif byt == 0xFF:
                # End
                if ret_ptr is not None:
                    c_ptr = ret_ptr
                    ret_ptr = None
                    debug_msg = f"Returning to {hex(c_ptr)} from subroutine"
                else:
                    _logger.info(f"Encountered end {hex(byt)}")
                    break
            elif cmd < 0xC:
                # Note
                score.append(
                    (NOTES[cmd % 12], octave_exp, (1 + arg) / speed_multiplier)
                )
                debug_msg = f"Note {NOTES[cmd % 12]}"
            elif cmd == 0xC:
                # Rest
                score.append(("r", None, (1 + arg) / speed_multiplier))
                debug_msg = "Rest"
            elif cmd == 0xE:
                # Octave modifier
                octave_exp = 8 - arg
                debug_msg = "Octave"
            else:
                _logger.warning(f"Encountered unknown byte {hex(byt)}")
                debug_msg = ""
                continue

            _logger.debug(f"{hex(prev_c_ptr)}\t{debug_msg} {hex(byt)}")
        _logger.info(
            "Obtained score with total duration %f", sum(note[2] for note in score)
        )

        return score
