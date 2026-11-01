"""Sound track for the 빵빵 블록 promo, built from out/events.json -> out/music.wav"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'out', 'events.json')))
DUR, EV = data['duration'], data['events']
SR = 44100; N = int(SR * (DUR + .5)); mix = np.zeros(N)
at = lambda name, d=DUR: next((e[1] for e in EV if e[0] == name), d)
mtof = lambda n: 440.0 * 2 ** ((n - 69) / 12)

def osc(kind, f, n, f2=None):
    t = np.arange(n) / SR
    fr = f if f2 is None else f * (f2 / f) ** (t / (n / SR))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return {'sine': np.sin(ph), 'square': np.sign(np.sin(ph)) * .6, 'tri': 2 / np.pi * np.arcsin(np.sin(ph))}.get(kind, np.random.uniform(-1, 1, n))
def env(n, r):
    t = np.arange(n) / SR; return np.minimum(1, t / .006) * np.exp(-t / r)
def add(t0, sig, g):
    i = int(t0 * SR); j = min(N, i + len(sig))
    if 0 <= i < N: mix[i:j] += sig[:j - i] * g
def tone(t0, kind, f, d, g, r=None, f2=None):
    n = int(d * SR); add(t0, osc(kind, f, n, f2) * env(n, r or d / 3), g)

# calm pentatonic loop (the game's own BGM style), 92 bpm, until the burn
STEP = 60 / 92 / 2; PENTA = [60, 62, 64, 67, 69, 72, 74, 76]; BASS = [48, 45, 41, 43]
rng = np.random.default_rng(7)
def bgm(t0, t1, gain=1.0):
    t, step = t0, 0
    while t < t1 - .05:
        bar, s = (step // 8) % 4, step % 8
        if s == 0: tone(t, 'tri', mtof(BASS[bar]), STEP * 7, .22 * gain)
        if s == 4: tone(t, 'tri', mtof(BASS[bar] + 7), STEP * 3, .1 * gain)
        if s % 2 == 0: tone(t, 'sine', 130, .12, .25 * gain, r=.04, f2=50)            # soft kick so it moves on a phone speaker
        if rng.random() < .6: tone(t, 'sine', mtof(PENTA[rng.integers(len(PENTA))]), STEP * 1.8, .08 * gain)
        step += 1; t += STEP
bgm(0, at('over'))
bgm(at('endcard'), DUR + .3, gain=.9)

def place(t): tone(t, 'sine', 180, .1, .35, f2=90); tone(t, 'square', 900, .03, .04)
def chimes(t, n):
    base = [523, 659, 784, 1047, 1319, 1568]
    for i in range(min(6, 2 + n)): tone(t + i * .06, 'square', base[i] * (1 + min(n, 6) * .03), .18, .07)
    tone(t, 'sine', 120, .25, .4, f2=50)
for name, t in EV:
    if name == 'start': [tone(t + i * .07, 'square', f, .09, .06) for i, f in enumerate([523, 659, 784])]
    elif name == 'clear': place(t); chimes(t, 1)
    elif name == 'clear3': place(t); chimes(t, 5)
    elif name == 'pigeon': tone(t, 'sine', 320, .12, .18); tone(t + .15, 'sine', 270, .16, .18)
    elif name == 'splat': tone(t, 'square', 110, .22, .14, f2=55); tone(t, 'sine', 70, .3, .35, f2=40)
    elif name == 'clearpoop': place(t); chimes(t, 2)
    elif name == 'gold': place(t); chimes(t, 3); [tone(t + .2 + i * .05, 'tri', f, .2, .09) for i, f in enumerate([1047, 1319, 1568, 2093])]
    elif name == 'misdrop': tone(t, 'tri', 300, .12, .12, f2=180)
    elif name == 'over': [tone(t + i * .16, 'tri', f, .32, .14) for i, f in enumerate([392, 330, 262, 196])]
    elif name == 'endcard': [tone(t + i * .09, 'square', f, .16, .07) for i, f in enumerate([523, 659, 784, 1047, 1319])]

mix = np.tanh(mix * 1.6) * .85
fade = int(.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
d = int(.012 * SR); right = np.concatenate([np.zeros(d), mix[:-d]]) * .95 + mix * .05
st = (np.stack([mix, right], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, 'out', 'music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('music.wav', round(N / SR, 2), 's')
