from typing import List, Optional, Tuple

import numpy as np
import scipy.signal
import simpleaudio

from .const import NOTE_FREQS, NOTES


class Player:
    def __init__(self, fs: int, volume: float = 2**12, waveform: str = "sawtooth"):
        self.fs = fs
        self.volume = volume
        if hasattr(scipy.signal, waveform):
            self.wavefn = getattr(scipy.signal, waveform)
        else:
            self.wavefn = getattr(np, waveform)

        self.play_obj = None

    def get_wave(
        self,
        score: List[Tuple[str, Optional[int], float]],
        octave_offset: int = 5,
        speed: float = 1.5,
        cut: float = 0.01,
    ):
        durs = [speed * note[2] / 16 for note in score]
        total_dur = sum(durs)
        t = np.linspace(0, total_dur, round(total_dur * self.fs), endpoint=False)
        w = np.zeros(t.shape)

        a = 0
        b = 0
        for i, (note, octave, _) in enumerate(score):
            a = b
            b = round(sum(durs[: i + 1]) * self.fs)
            b_prime = b - round(cut * self.fs)
            if note == "r":
                freq = 0
            else:
                freq = 2 ** (octave - octave_offset) * NOTE_FREQS[NOTES.index(note)]
            w[a:b_prime] = self.volume * self.wavefn(t[a:b_prime] * freq * 2 * np.pi)

        return w.astype(np.int16)

    def play_score(self, score: List[Tuple[str, Optional[int], float]], **kwargs):
        self.stop()
        w = self.get_wave(score, **kwargs)
        self.play_obj = simpleaudio.play_buffer(w, 1, 2, self.fs)

    def play_wave(self, w: np.array):
        self.stop()
        self.play_obj = simpleaudio.play_buffer(w, 1, 2, self.fs)

    def stop(self):
        if self.play_obj:
            self.play_obj.stop()
