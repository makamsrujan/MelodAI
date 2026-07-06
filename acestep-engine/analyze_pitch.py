"""Rough vocal-pitch estimate to sanity-check male vs female generation.
Female vocals typically median F0 ~180-260Hz; male ~90-160Hz."""
import sys
import numpy as np
import librosa


def median_f0(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    # pyin gives per-frame F0 with voiced flags; restrict to a wide vocal range
    f0, voiced, _ = librosa.pyin(
        y, fmin=80, fmax=400, sr=sr, frame_length=2048
    )
    vals = f0[~np.isnan(f0)]
    if len(vals) == 0:
        return None
    return float(np.median(vals)), len(vals)


for p in sys.argv[1:]:
    res = median_f0(p)
    if res is None:
        print(f"{p}: no pitched content detected")
    else:
        med, n = res
        guess = "FEMALE" if med >= 165 else "male"
        print(f"{p.split('/')[-1]}: median F0 = {med:.0f} Hz  -> likely {guess}  ({n} voiced frames)")
