"""Single source of truth for timing. Video and audio both read this file."""

FPS = 30
DURATION = 60.0
BPM = 120.0
BEAT = 60.0 / BPM          # 0.5 s
BAR = 4 * BEAT             # 2.0 s

TITLE_CPS = 34.0           # characters per second for titles
SUB_CPS = 52.0             # characters per second for sub lines

# ------------------------------------------------------------------ eras
# name, start, end.  Transitions are listed separately.
ERAS = [
    ('term', 0.0, 3.85),
    ('paper', 3.85, 14.0),
    ('winter', 14.0, 16.0),
    ('amber', 16.0, 18.0),
    ('green', 18.0, 23.05),
    ('neon', 23.05, 31.0),
    ('synth', 31.0, 41.0),
    ('clean', 41.0, 47.95),
    ('dusk', 47.95, 60.0),
]

# (time of cut, kind, half-width in seconds)
TRANSITIONS = [
    (3.85, 'wipe', 0.30),
    (14.0, 'dissolve', 0.22),
    (16.0, 'crt', 0.20),
    (18.0, 'glitch', 0.10),
    (23.05, 'flood', 0.30),
    (31.0, 'glitchdissolve', 0.16),
    (41.0, 'flash', 0.12),
    (47.95, 'dissolve', 0.40),
]

SKILLS = ['LEARN', 'TALK', 'PLAY', 'READ', 'SEE', 'IMAGINE', 'INTUIT', 'ATTEND',
          'WRITE', 'FOLD', 'CHAT', 'DRAW', 'REASON', 'CODE', 'ACT']

# ------------------------------------------------------------------ scenes
# u_* values are local times (seconds after t0).
SCENES = [
    dict(id='neuron', t0=4.0, t1=6.0, era='paper', year=1943,
         title='McCulloch & Pitts', sub=['a neuron, written as logic']),
    dict(id='turing', win=1.4, t0=6.0, t1=8.0, era='paper', year=1950,
         title='The Imitation Game', sub=['Alan Turing asks:', 'can machines think?']),
    dict(id='dartmouth', win=1.55, t0=8.0, t1=10.0, era='paper', year=1956,
         title='Dartmouth Workshop', sub=['a new field gets its name']),
    dict(id='perceptron', win=1.35, t0=10.0, t1=12.0, era='paper', year=1958,
         title='The Perceptron', sub=['Rosenblatt: a machine', 'that learns from data'],
         skills=[(1.55, 'LEARN', 1)]),
    dict(id='eliza', win=1.45, t0=12.0, t1=14.0, era='paper', year=1966,
         title='ELIZA', sub=['Weizenbaum, MIT', 'an early chatbot'],
         skills=[(1.45, 'TALK', 1)]),
    dict(id='winter', t0=14.0, t1=16.0, era='winter', year=1973,
         title='The first AI winter', sub=['Lighthill Report:', 'the funding freezes']),
    dict(id='backprop', win=1.3, t0=16.0, t1=18.0, era='amber', year=1986,
         title='Backpropagation', sub=['Rumelhart, Hinton', '& Williams'],
         skills=[(1.62, 'LEARN', 2)]),
    dict(id='deepblue', win=1.4, t0=18.0, t1=20.0, era='green', year=1997,
         title='Deep Blue', sub=['IBM machine beats world', 'champion Garry Kasparov'],
         skills=[(1.35, 'PLAY', 1)]),
    dict(id='lenet', win=1.3, t0=20.0, t1=22.0, era='green', year=1998,
         title='LeNet', sub=['Yann LeCun: a network', 'reads handwriting'],
         skills=[(1.5, 'READ', 1)]),
    dict(id='imagenet', t0=22.0, t1=23.3, era='green', year=2009,
         title='ImageNet', sub=['millions of labeled', 'images'], era2='neon'),
    dict(id='alexnet', win=1.3, t0=23.3, t1=25.0, era='neon', year=2012,
         title='AlexNet', sub=['top-5 error 15.3%,', 'deep learning ignites'],
         skills=[(1.2, 'SEE', 1)]),
    dict(id='gan', win=1.45, t0=25.0, t1=27.0, era='neon', year=2014,
         title='GANs', sub=['two networks duel:', 'one learns to create'],
         skills=[(1.55, 'IMAGINE', 1)]),
    dict(id='alphago', win=1.35, t0=27.0, t1=29.0, era='neon', year=2016,
         title='AlphaGo', sub=['beats Lee Sedol 4-1', 'with Move 37'],
         skills=[(1.5, 'INTUIT', 1)]),
    dict(id='transformer', win=1.4, t0=29.0, t1=31.0, era='neon', year=2017,
         title='Attention Is All You Need', sub=['the Transformer'],
         skills=[(1.35, 'ATTEND', 1)]),
    dict(id='gpt3', win=1.0, t0=31.0, t1=32.5, era='synth', year=2020,
         title='GPT-3', sub=['175 billion parameters'],
         skills=[(0.95, 'WRITE', 1)]),
    dict(id='alphafold', win=1.1, t0=32.5, t1=34.0, era='synth', year=2020,
         title='AlphaFold 2', sub=['predicts how proteins', 'fold'],
         skills=[(1.05, 'FOLD', 1)]),
    dict(id='chatgpt', win=0.8, t0=34.0, t1=36.0, era='synth', year=2022,
         title='ChatGPT', sub=['AI goes mainstream:', '100M users in 2 months'],
         skills=[(0.75, 'CHAT', 1)]),
    dict(id='diffusion', win=1.5, t0=36.0, t1=38.0, era='synth', year=2022,
         title='Diffusion models', sub=['DALL·E 2 & Stable', 'Diffusion: text to image'],
         skills=[(1.55, 'DRAW', 1)]),
    dict(id='frontier', win=1.2, t0=38.0, t1=39.4, era='synth', year=2023,
         title='GPT-4, Claude & Llama', sub=['the frontier race begins']),
    dict(id='reasoning', win=1.3, t0=39.4, t1=41.0, era='synth', year=2024,
         title='Reasoning models', sub=['think before answering', '+ two Nobel Prizes'],
         skills=[(1.25, 'REASON', 1)]),
    dict(id='agents', win=3.2, t0=41.0, t1=45.0, era='clean', year=2025,
         title='AI agents', sub=['that reason, write code', 'and act on computers'],
         years=[(2.0, 2026)],
         skills=[(1.25, 'CODE', 1), (2.55, 'ACT', 1)]),
]

# ------------------------------------------------------------------ the hero
BIRTH_T = 5.2                      # the neuron hatches: LV 1
EVOLVE = [(11.42, 'PERCEPTRON'), (17.36, 'NEURAL KNIGHT'), (23.72, 'DEEP SEER'),
          (29.18, 'TRANSFORMER DRAKE'), (31.45, 'FOUNDATION TITAN'), (41.12, 'AGENT')]
EVOLVE_DUR = 0.6
# hit points (keys are linearly interpolated); a level-up restores HP
HP_KEYS = [(0, 1), (7.0, 1), (7.08, 0.86), (7.4, 0.86), (7.7, 1), (14.45, 1), (15.35, 0.04),
           (16.15, 0.04), (16.8, 1), (18.9, 1), (18.98, 0.8), (19.4, 0.8), (19.7, 1),
           (27.5, 1), (27.58, 0.86), (28.35, 0.86), (28.65, 1)]
WALK = 0.32                        # the hero walks at the start of each scene


def wins():
    out = [BIRTH_T]
    for s in SCENES:
        if s.get('win') is not None:
            out.append(s['t0'] + s['win'])
    return sorted(out)


def level(t):
    return sum(1 for w in wins() if w <= t)


def form(t):
    f = 'SPARK'
    for (te, name) in EVOLVE:
        if t >= te + EVOLVE_DUR * 0.5:
            f = name
    return f


QUESTION_T0 = 45.0
YUNAGI_T0 = 47.95
END_T0 = 55.8


def scene_by_id(i):
    for s in SCENES:
        if s['id'] == i:
            return s
    raise KeyError(i)


def year_events():
    """List of (t, from_year, to_year) odometer rolls."""
    ev = []
    prev = 1900
    for s in SCENES:
        if s['year'] != prev:
            ev.append((s['t0'], prev, s['year']))
            prev = s['year']
        for (u, y) in s.get('years', []):
            ev.append((s['t0'] + u, prev, y))
            prev = y
    return ev


YEAR_ROLL = 0.38


def unlock_events():
    """(t, skill, level) in time order."""
    ev = []
    for s in SCENES:
        for (u, name, lvl) in s.get('skills', []):
            ev.append((s['t0'] + u, name, lvl))
    return sorted(ev)


def text_events(s):
    """Typing schedule for a scene: list of (line_index, start, n_chars, cps)."""
    out = []
    t = s['t0'] + 0.1
    out.append((0, t, len(s['title']), TITLE_CPS))
    t += len(s['title']) / TITLE_CPS + 0.05
    for i, line in enumerate(s['sub']):
        out.append((i + 1, t, len(line), SUB_CPS))
        t += len(line) / SUB_CPS + 0.03
    return out


# Extra timed text for the intro / question
INTRO_Q = 'What can AI do?'
INTRO_Q_T = 0.75
INTRO_Q_CPS = 11.0
INTRO_SUB = 'a short history, in pixels'
INTRO_SUB_T = 2.35
INTRO_SUB_CPS = 34.0

Q_LINE1_T = 45.3
Q_LINE1_CPS = 26.0
Q_FORMS_T = 45.75
Q_FORM_STEP = 0.085
Q_ICONS_T = 46.4
Q_ICON_STEP = 0.032
Q_LINE2 = 'What will you build with it?'
Q_LINE2_T = 47.0
Q_LINE2_CPS = 40.0

CARD_TIMES = [49.85, 50.55, 51.25]
MAP_T = 52.85
