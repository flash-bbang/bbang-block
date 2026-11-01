"""Upbeat chiptune-pop sound track for the 빵빵 블록 reel -> out/music2.wav
124 bpm, C major, F - G - Em - Am loop with a hummable lead, bouncy bass, offbeat chord plucks and a full kit.
"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'out', 'events.json')))
DUR, EV = data['duration'], data['events']
SR = 44100; N = int(SR * (DUR + .6))
at = lambda name, d=DUR: next((e[1] for e in EV if e[0] == name), d)
mtof = lambda n: 440.0 * 2 ** ((n - 69) / 12)
T_START, T_OVER, T_END = at('start', 1.6), at('over'), at('endcard')

bus = {k: np.zeros(N) for k in ('drums', 'bass', 'chords', 'lead', 'sfx')}
def add(name, t0, sig, g=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    a, b = max(0, i), min(N, i + len(sig)); bus[name][a:b] += sig[a - i:b - i] * g

def env(n, a=.004, d=None, sustain=0.0):
    t = np.arange(n) / SR; d = d or n / SR / 2
    e = np.minimum(1, t / a) * (sustain + (1 - sustain) * np.exp(-t / d))
    rel = min(n, int(.03 * SR)); e[-rel:] *= np.linspace(1, 0, rel); return e
def wave_(kind, f, n, vib=0.0, f_end=None):
    t = np.arange(n) / SR
    fr = np.full(n, f) if f_end is None else f * (f_end / f) ** (t / (n / SR))
    if vib: fr = fr * (1 + vib * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / .12))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    if kind == 'sine': return np.sin(ph)
    if kind == 'tri': return 2 / np.pi * np.arcsin(np.sin(ph))
    if kind == 'saw': return ((ph / np.pi) % 2 - 1)
    if kind == 'pulse': return np.where((ph / (2 * np.pi)) % 1 < .25, 1.0, -1.0) * .7   # 25% duty, the classic chip lead
    if kind == 'square': return np.sign(np.sin(ph)) * .7
def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y
noise = np.random.default_rng(3).uniform(-1, 1, int(SR * .5))

# ----- instruments -----
def kick(t, g=1.0):
    n = int(.28 * SR); add('drums', t, wave_('sine', 150, n, f_end=42) * env(n, .001, .09), .95 * g)
def snare(t, g=1.0):
    n = int(.2 * SR); body = wave_('tri', 210, n, f_end=160) * env(n, .001, .05)
    nz = noise[:n] - lowpass(noise[:n], 1800); add('drums', t, (body * .5 + nz * env(n, .001, .07)), .55 * g)
def hat(t, g=1.0, open_=False):
    n = int((.22 if open_ else .05) * SR); nz = noise[:n] - lowpass(noise[:n], 7000)
    add('drums', t, nz * env(n, .001, .09 if open_ else .015), .17 * g)
def bass(t, note, dur):
    n = int(dur * SR); s = lowpass(wave_('saw', mtof(note), n), 900) * 1.6 + wave_('tri', mtof(note), n) * .5
    add('bass', t, s * env(n, .004, dur * .7, .4), .42)
def pluck(t, notes, dur):
    n = int(dur * SR)
    for k in notes: add('chords', t, (wave_('tri', mtof(k), n) * .6 + wave_('square', mtof(k), n) * .15) * env(n, .003, .09), .16)
def lead(t, note, dur, g=1.0):
    n = int(dur * SR); s = wave_('pulse', mtof(note), n, vib=.006) * env(n, .006, dur * .8, .55)
    add('lead', t, s, .2 * g)
    add('lead', t + .18, s * .5, .2 * g * .35)   # dotted echo

# ----- song -----
BPM = 124; BEAT = 60 / BPM; S16 = BEAT / 4; BAR = BEAT * 4
CHORDS = [[53, 57, 60, 64], [55, 59, 62, 67], [52, 55, 59, 62], [57, 60, 64, 67]]    # Fmaj7 G Em7 Am7
ROOTS = [41, 43, 40, 45]
_ = None
MEL = [  # 8 bars of eighth notes
    [76, _, 79, 76, _, 72, 74, 76], [74, _, 71, 74, 79, _, 77, 76],
    [76, _, 79, 83, _, 81, 79, 76], [81, _, _, 79, 76, _, 72, _],
    [76, _, 79, 76, _, 72, 74, 76], [74, _, 79, _, 83, 81, 79, 74],
    [76, 79, 76, 74, 72, _, 76, _], [72, _, _, _, 71, _, 74, _],
]

def section(t0, t1, drums=True, melody=True, intensity=1.0, bar0=0):
    bar = bar0; t = t0
    while t < t1 - .02:
        ci = bar % 4; ch = CHORDS[ci]; root = ROOTS[ci]
        for s in range(16):
            ts = t + s * S16 + (S16 * .12 if s % 2 else 0)      # a touch of swing
            if ts >= t1: break
            if drums:
                if s in (0, 8) or (s == 14 and bar % 2): kick(ts, intensity)
                if s in (4, 12): snare(ts, intensity)
                if s % 2 == 0: hat(ts, .6 + (.4 if s % 4 == 2 else 0))
                if s == 14 and bar % 4 == 3: hat(ts, 1, open_=True)
            if s % 2 == 0: bass(ts, root + (12 if s % 4 == 2 else 0), S16 * 1.8)
            if s in (2, 6, 10, 14): pluck(ts, ch, S16 * 1.6)
            if melody and s % 2 == 0:
                nt = MEL[bar % 8][s // 2]
                if nt:
                    ln = 1
                    while s // 2 + ln < 8 and MEL[bar % 8][s // 2 + ln] is None: ln += 1
                    lead(ts, nt, S16 * 2 * ln * .92)
        bar += 1; t += BAR
    return bar

# intro on the start screen: plucks + bass only, then a snare fill into the drop
section(0, T_START, drums=False, melody=False)
for k in range(4): snare(T_START - BEAT + k * S16, .5 + k * .15)
b = section(T_START, T_OVER)
# the burn: everything stops, sad descending stab, then the end card restarts the hook
# comic "wah wah wah waaah" on a muted brass-ish voice, over a soft minor pad
kick(T_OVER, 1.1)
wah = [(0.00, 62, .42), (0.48, 61, .42), (0.96, 60, .42), (1.44, 59, 1.35)]
for dt, nt, dur in wah:
    n = int(dur * SR); t = np.arange(n) / SR
    f = mtof(nt) * (1 - .03 * np.minimum(1, t / dur) * (dur > 1)) * (1 + .012 * np.sin(2 * np.pi * 6 * t) * (dur > 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = lowpass(((ph / np.pi) % 2 - 1), 700 + 900 * np.abs(np.sin(np.pi * t / min(dur, .42))).mean())
    add('lead', T_OVER + .15 + dt, tone * env(n, .03, dur * .9, .6) * 2.2, .3)
for k in (53, 56, 60):                                       # F minor pad under it
    n = int((T_END - T_OVER) * SR); add('chords', T_OVER, lowpass(wave_('saw', mtof(k), n), 600) * env(n, .25, 2.5, .5), .12)
section(T_END, DUR + .5, bar0=0)

# ----- sound effects from the edit -----
def sfx_tone(t, kind, f, d, g, f_end=None):
    n = int(d * SR); add('sfx', t, wave_(kind, f, n, f_end=f_end) * env(n, .003, d / 3), g)
def chimes(t, n):
    base = [523, 659, 784, 1047, 1319, 1568]
    for i in range(min(6, 2 + n)): sfx_tone(t + i * .055, 'square', base[i] * 2, .14, .05)
for name, t in EV:
    if name in ('clear', 'clear3', 'clearpoop', 'gold'):
        sfx_tone(t, 'sine', 200, .1, .3, 90); chimes(t, {'clear': 1, 'clear3': 5, 'clearpoop': 2, 'gold': 3}[name])
    if name == 'gold': [sfx_tone(t + .22 + i * .05, 'tri', f, .2, .08) for i, f in enumerate([1568, 2093, 2637, 3136])]
    if name == 'pigeon': sfx_tone(t, 'sine', 320, .12, .2); sfx_tone(t + .15, 'sine', 270, .16, .2)
    if name == 'splat': sfx_tone(t, 'square', 110, .2, .12, 55); sfx_tone(t, 'sine', 70, .28, .3, 40)
    if name == 'misdrop': sfx_tone(t, 'tri', 320, .12, .12, 180)

# ----- mix: sidechain the bass and chords to the kick, then glue -----
duck = np.ones(N)
step = BEAT / 2
t = T_START
while t < T_OVER:
    i = int(t * SR); n = int(.16 * SR); duck[i:i + n] = np.minimum(duck[i:i + n], 1 - .55 * np.exp(-np.arange(min(n, N - i)) / SR / .06)[:len(duck[i:i + n])])
    t += BEAT * 2
mix = bus['drums'] + (bus['bass'] + bus['chords']) * duck + bus['lead'] + bus['sfx']
mix = mix / (np.percentile(np.abs(mix), 99.5) + 1e-9) * .8
mix = np.tanh(mix * 1.3) / np.tanh(1.3) * .92
fade = int(.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
d = int(.011 * SR)
left = mix + np.concatenate([np.zeros(d), bus['lead'][:-d]]) * .08
right = mix + np.concatenate([np.zeros(d), bus['chords'][:-d]]) * .08
st = np.clip(np.stack([left, right], 1), -1, 1)
with wave.open(os.path.join(HERE, 'out', 'music2.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('music2.wav', round(N / SR, 2), 's')
