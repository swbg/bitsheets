import numpy as np
import scipy.signal
import simpleaudio

from .const import NOTE_FREQS, NOTES
from .types import ScoresType, ScoreType


class Player:
    def __init__(self, fs: int, volume: float = 2**12, waveform: str = "sawtooth"):
        """
        Class for playing parsed scores.

        :param fs: Sampling rate
        :param volume: Sound volume (amplitude multiplier)
        :param waveform: Waveform function to use
        """
        self.fs = fs
        self.volume = volume
        if hasattr(scipy.signal, waveform):
            self.wavefn = getattr(scipy.signal, waveform)
        else:
            self.wavefn = getattr(np, waveform)

        self.play_obj = None

    def get_wave(
        self,
        score: ScoreType,
        octave_offset: int = 5,
        speed: float = 1.5,
        cut: float = 0.01,
    ):
        """
        Create wave from parsed score.

        :param score: Parsed score
        :param octave_offset: Overall octave offset
        :param speed: Speed multiplier
        :param cut: Time of silence between two notes
        """
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

    def get_waves(self, scores: ScoresType, *args, **kwargs):
        """
        Create waves from parsed scores.

        :param score: Parsed score
        """
        return [self.get_wave(score, *args, **kwargs) for score in scores]

    def play_score(self, score: ScoreType, **kwargs):
        """
        Play a parsed score.

        :param score: Parsed score
        """
        self.stop()
        w = self.get_wave(score, **kwargs)
        self.play_obj = simpleaudio.play_buffer(w, 1, 2, self.fs)

    def play_wave(self, w: np.array):
        """
        Play a wave array.

        :param w: Wave array
        """
        self.stop()
        self.play_obj = simpleaudio.play_buffer(w, 1, 2, self.fs)

    def stop(self):
        """
        Stop playing.
        """
        if self.play_obj:
            self.play_obj.stop()

    def wait_done(self):
        """
        Wait until playing is done.
        """
        if self.play_obj:
            self.play_obj.wait_done()
