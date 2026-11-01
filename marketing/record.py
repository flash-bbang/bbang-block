"""Record the 빵빵 블록 promo on a virtual clock.
python3 record.py preview  -> stills in out/stills
python3 record.py full     -> out/promo_silent.mp4 + out/events.json
"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'preview'
FPS, DT = 30, 1000 / 30

CLOCK = r"""
(() => {
  let now = 0; const raf = []; const timers = []; let tid = 1;
  performance.now = () => now;
  window.requestAnimationFrame = cb => { raf.push(cb); return raf.length; };
  window.setTimeout = (cb, ms, ...a) => { const id = tid++; timers.push({id, at: now + (+ms || 0), cb: () => cb(...a)}); return id; };
  window.clearTimeout = id => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); };
  window.setInterval = () => 0;
  window.__tick = ms => {
    now += ms;
    timers.sort((a, b) => a.at - b.at);
    while (timers.length && timers[0].at <= now){ const t = timers.shift(); try { t.cb(); } catch(e){ console.error(e); } }
    raf.splice(0).forEach(cb => { try { cb(now); } catch(e){ console.error(e); } });
  };
})();
"""
KIND = {'.': -1, 'P': 6, 'G': 7}

def board_js(rows):
    assert len(rows) == 8 and all(len(r) == 8 for r in rows), rows
    return json.dumps([[KIND.get(ch, int(ch) if ch.isdigit() else -1) for ch in r] for r in rows])

events, t_ms = [], 0.0

def main():
    global t_ms
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        page = browser.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
        page.on('pageerror', lambda e: print('PAGE EXCEPTION:', e))
        page.add_init_script(CLOCK)
        page.goto('file://' + os.path.join(HERE, 'rec.html'))
        page.wait_for_timeout(300)
        ev = lambda code: page.evaluate('c => window.__BB.ev(c)', code)
        cap = lambda html: page.evaluate('h => document.getElementById("cap").innerHTML = h', html)

        ff = None
        if MODE == 'full':
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                                   os.path.join(OUT, 'promo_silent.tmp.mp4')], stdin=subprocess.PIPE)

        def frames(n, still=None):
            global t_ms
            for i in range(n):
                page.evaluate('() => window.__tick(%f)' % DT)
                if ff: ff.stdin.write(page.screenshot(type='jpeg', quality=92))
                elif still and i == n - 1: page.screenshot(path=os.path.join(OUT, 'stills', still + '.png'))
                t_ms += DT

        def mark(name): events.append([name, round(t_ms / 1000, 3)])

        def finger(on, x=0, y=0):
            page.evaluate("""([on, x, y]) => { const f = document.getElementById('finger'), r = document.getElementById('c').getBoundingClientRect();
              f.style.display = on ? 'block' : 'none'; f.style.left = (r.left + x) + 'px'; f.style.top = (r.top + y) + 'px'; }""", [on, x, y])

        def setup(rows, tray, extra=''):
            # tray: list of (cells, kind)
            t = ', '.join(f"{{shape: SHAPES.find(s => JSON.stringify(s.cells) === JSON.stringify(norm({json.dumps(c)}))), kind: {k}}}" for c, k in tray)
            ev(f"board = {board_js(rows)}; tray = [{t}]; while (tray.length < 3) tray.push(null); pops = []; crumbs = []; texts = []; {extra}")

        def drag_to(i, gx, gy, n=30, release=True, name=None):
            """Animate a finger dragging tray piece i so it lands at grid (gx, gy)."""
            for f in range(n + 1):
                k = f / n; e = 2*k*k if k < .5 else 1 - (-2*k + 2)**2 / 2
                pos = ev(f"""(() => {{ const t = tray[{i}].shape, s = slotCenter({i}), lift = cell*2.1;
                    const tx = bx + {gx}*cell + t.wd*cell/2, ty = by + {gy}*cell + t.ht*cell/2 + lift;
                    const x = s.x + (tx - s.x)*{e}, y = s.y + (ty - s.y)*{e};
                    if (!drag) drag = {{i: {i}, lift}}; updateDrag(x, y); return [x, y]; }})()""")
                finger(True, pos[0], pos[1])
                frames(1)
            if release:
                ev("endDrag()"); finger(False)
                if name: mark(name)

        I2H = [[0,0],[1,0]]; I3V = [[0,0],[0,1],[0,2]]; I3H = [[0,0],[1,0],[2,0]]; O2 = [[0,0],[1,0],[0,1],[1,1]]; DOT = [[0,0]]; L3 = [[0,0],[0,1],[1,1]]

        # S0 hook
        ev("nick = '빵돌이'; nickEl.value = '빵돌이'; maybePigeon = function(){};")
        page.evaluate("document.querySelector('#start .sub').style.display = 'none'")
        cap('블록 퍼즐인데<br><em>식빵이 살아있음</em>')
        frames(48, still='s0')
        ev("$('start').hidden = true; newGame();"); mark('start')

        # S1 one line
        setup(["........", "........", "........", "........", "......1.", "..2...13", "4.2..113", "012..345"], [(I2H, 0), (L3, 3), (DOT, 2)])
        cap('줄을 채우면<br><em>웃으면서 터짐</em>')
        frames(10)
        drag_to(0, 3, 7, name='clear')
        frames(42, still='s1')

        # S2 three lines + combo
        setup(["........", "........", "...3....", "1..3..2.", "11.04.2.", "012345.1", "234501.2", "450123.3"], [(I3V, 4), (DOT, 1), (I2H, 5)], "combo = 1; sinceClear = 0;")
        cap('한 번에 여러 줄은<br><em>빵빵빵!!</em>')
        frames(10)
        drag_to(0, 6, 5, name='clear3')
        frames(48, still='s2')

        # S3 pigeon poop, then clear it
        setup(["........", "....1...", "..4.1...", "01.23..4", "01.230.4", "3..2...5", "35.21.05", "35.21105"], [(I2H, 1), (DOT, 3), (L3, 0)])
        cap('근데 비둘기가<br><em>똥 싸고 감</em>')
        ev("const t = [2, 3]; pigeon = {dir: 1, x: -50, y: by - cell*.2, tx: bx + (t[0] + .5)*cell, target: t, poop: null, done: false}; say('헉 비둘기다', 1400); sfx('coo');")
        mark('pigeon')
        for _ in range(150):
            frames(1)
            if ev("board[3][2] === 6"): mark('splat'); break
        frames(36, still='s3a')
        cap('똥은 줄로 지우면<br><em>+30점</em>')
        frames(8)
        drag_to(0, 5, 3, name='clearpoop')
        frames(44, still='s3b')

        # S4 golden toast
        setup(["......2.", "...12345", "....2.4.", ".....04.", "........", "........", "1......0", "12....30"], [(I3H, 7), (DOT, 2), (I2H, 4)])
        cap('황금빵이 터지면<br><em>점수 두 배</em>')
        frames(16)
        drag_to(0, 0, 1, name='gold')
        frames(46, still='s4')

        # S5 panic + a bad drop
        setup(["01.23.45", "2.345.01", "34.012.3", "450123..", "123.45.0", "4.01.234", ".0.23541", "0123.5.2"], [(O2, 3), (DOT, 1), (I2H, 0)], "danger = false; talk = null;")
        cap('판이 꽉 차면<br><em>식빵들이 겁먹음</em>')
        mark('panic')
        frames(52)
        drag_to(0, 3, 3, n=26, release=False)
        frames(6)
        ev("endDrag()"); finger(False); mark('misdrop')
        frames(44, still='s5')

        # S6 burnt
        cap('결국 다 태움 ㅋㅋ')
        ev("gameOver(); $('quip').textContent = '빵 다 탔어요';"); mark('over')
        frames(24)
        page.evaluate("document.getElementById('over').hidden = true")   # keep the burnt tray visible for a beat
        frames(40, still='s6')
        page.evaluate("document.getElementById('over').hidden = false")
        frames(30)

        # S7 end card
        cap('')
        page.evaluate("document.getElementById('over').hidden = true; document.getElementById('endcard').hidden = false")
        mark('endcard')
        frames(96, still='s7')

        if ff:
            ff.stdin.close(); code = ff.wait()
            if code == 0: os.replace(os.path.join(OUT, 'promo_silent.tmp.mp4'), os.path.join(OUT, 'promo_silent.mp4'))
            print('ffmpeg exit', code)
        json.dump({'duration': round(t_ms / 1000, 3), 'events': events}, open(os.path.join(OUT, 'events.json'), 'w'), indent=1)
        print('duration', round(t_ms / 1000, 2), 's', events)
        browser.close()

main()
