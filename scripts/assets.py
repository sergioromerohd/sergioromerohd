#!/usr/bin/env python3
"""Genera los SVG del perfil (banner, stack, stats) con la estética de cv.sergioromerohd.com.

    python3 scripts/assets.py banner    # assets/banner.svg + banner-m.svg
    python3 scripts/assets.py stack     # assets/stack.svg  + stack-m.svg   (iconos: scripts/icons.json)
    python3 scripts/assets.py stats     # assets/stats.svg  + stats-m.svg    (necesita GH_TOKEN)
    python3 scripts/assets.py all

Sin dependencias: solo librería estándar. Cada SVG tiene variante ancha (escritorio) y estrecha
(-m, móvil); el README elige con <picture>. Las animaciones son CSS y respetan
prefers-reduced-motion; sin animación el estado base ya es el final (todo visible).
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets")

# Tokens de diseño: los del portfolio (app/globals.css), solo modo oscuro.
CARD, BAR, BORDER = "#0b111e", "#0e1524", "#20283c"
FG, MUTED, TEAL, DIM = "#f1f5f9", "#94a3b8", "#35e9da", "#2a3450"
MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"

BASE_CSS = (
    "text{font-family:" + MONO + ";font-variant-ligatures:none}"
    ".t{animation:pop 1ms linear var(--d) backwards}"
    ".f{animation:fade .55s ease-out var(--d) backwards}"
    "@keyframes pop{from{opacity:0}}"
    "@keyframes fade{from{opacity:0;transform:translateY(5px)}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


# ───────────────────────── utilidades ─────────────────────────
def svg(w, h, body, title, desc, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d">\n<title id="t">{escape(title)}</title>'
        f'<desc id="d">{escape(desc)}</desc>\n<style>{BASE_CSS}{css}</style>\n{body}\n</svg>\n'
    )


def window(w, h, title):
    """Marco de terminal: tarjeta, barra de título con tres puntos y título centrado."""
    r = 10
    return (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{CARD}" stroke="{BORDER}"/>'
        f'<path d="M.5 36V{r + .5}a{r} {r} 0 0 1 {r} -{r}H{w - r - .5}a{r} {r} 0 0 1 {r} {r}V36Z" fill="{BAR}"/>'
        f'<path d="M.5 36.5H{w - .5}" stroke="{BORDER}"/>'
        f'<g fill="{DIM}"><circle cx="22" cy="18.5" r="5"/><circle cx="40" cy="18.5" r="5"/>'
        f'<circle cx="58" cy="18.5" r="5"/></g>'
        f'<text x="{w / 2}" y="22.5" text-anchor="middle" fill="{MUTED}" font-size="12">{escape(title)}</text>'
    )


def grid(w, h, axis):
    """Cuadrícula tenue (el .grid-bg del portfolio) que se difumina hacia la zona de texto."""
    if axis == "x":
        gx = '<linearGradient id="gm" x1="0" x2="1" y1="0" y2="0"><stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
    else:
        gx = '<linearGradient id="gm" x1="0" x2="0" y1="0" y2="1"><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
    return (
        f'<defs><pattern id="gp" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0H0V24" fill="none" stroke="{BORDER}" stroke-opacity=".6"/></pattern>{gx}'
        f'<mask id="gk"><rect x="1" y="37" width="{w - 2}" height="{h - 38}" rx="9" fill="url(#gm)"/></mask></defs>'
        f'<rect x="1" y="37" width="{w - 2}" height="{h - 38}" rx="9" fill="url(#gp)" mask="url(#gk)"/>'
    )


def prompt(x, y, fs, t):
    return f'<text class="t" style="--d:{t:.3f}s" x="{x}" y="{y}" font-size="{fs}" fill="{TEAL}">$</text>'


def typed(text, x, y, fs, color, t0, step):
    """Texto tecleado carácter a carácter (cada carácter es un <text> con su retardo)."""
    cw, out = fs * 0.6, []
    for i, ch in enumerate(text):
        if ch != " ":
            out.append(
                f'<text class="t" style="--d:{t0 + i * step:.3f}s" x="{x + i * cw:.2f}" y="{y}" '
                f'font-size="{fs}" fill="{color}">{escape(ch)}</text>'
            )
    return "".join(out)


def caret(name, x, y, fs, n, t0, step):
    """Cursor que avanza n pasos mientras se teclea y desaparece al terminar."""
    cw = fs * 0.6
    css = (
        f"@keyframes {name}{{0%{{opacity:0;transform:translateX(0)}}.1%{{opacity:1;transform:translateX(0)}}"
        f"100%{{opacity:1;transform:translateX({n * cw:.2f}px)}}}}"
        f".{name}{{opacity:0;animation:{name} {n * step:.3f}s steps({n},start) {t0:.3f}s backwards}}"
    )
    el = f'<rect class="{name}" x="{x:.2f}" y="{y - fs * .86:.2f}" width="{cw * .9:.2f}" height="{fs * 1.14:.2f}" fill="{TEAL}"/>'
    return el, css


# ───────────────────────── banner ─────────────────────────
# Bandas de tercio de octava (ISO, 50 Hz – 10 kHz): guiño a ACTUA (sonometría) e IRMA (vibraciones).
BANDS = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000]
LEVELS = [.18, .27, .33, .46, .50, .63, .58, .77, .72, .86, .80, .91, .84, 1.0, .87, .79, .71, .60, .49, .41, .30, .24, .15, .11]
PEAK = BANDS.index(1000)

SPECTRUM_CSS = (
    ".bar{transform-box:fill-box;transform-origin:50% 100%;"
    "animation:rise .8s cubic-bezier(.2,.8,.2,1) var(--d) backwards,breathe var(--p) ease-in-out var(--b) infinite alternate}"
    ".pk{animation:rise .8s cubic-bezier(.2,.8,.2,1) var(--d) backwards}"
    "@keyframes rise{from{transform:scaleY(.04)}}"
    "@keyframes breathe{from{transform:scaleY(1)}to{transform:scaleY(.84)}}"
)


def spectrum(x0, x1, base, maxh, t0):
    n, pitch = len(LEVELS), (x1 - x0) / len(LEVELS)
    bw = pitch * 0.62
    out = [f'<path d="M{x0} {base + .5}H{x1}" stroke="{BORDER}"/>']
    for i, lv in enumerate(LEVELS):
        h, x = max(3, lv * maxh), x0 + i * pitch + (pitch - bw) / 2
        d = t0 + i * 0.035
        op = 1 if i == PEAK else 0.28 + 0.30 * lv
        out.append(
            f'<rect class="bar{" pk" if i == PEAK else ""}" style="--d:{d:.3f}s;--b:{d + .9:.3f}s;--p:{2.4 + (i % 5) * .37:.2f}s" '
            f'x="{x:.2f}" y="{base - h:.2f}" width="{bw:.2f}" height="{h:.2f}" rx="1.6" fill="{TEAL}" fill-opacity="{op:.2f}"/>'
        )
    px = x0 + PEAK * pitch + pitch / 2
    out.append(f'<text x="{x0}" y="{base + 16}" font-size="9" fill="{MUTED}">50 Hz</text>')
    out.append(f'<text x="{px:.1f}" y="{base + 16}" font-size="9" fill="{TEAL}" text-anchor="middle">1 kHz</text>')
    out.append(f'<text x="{x1}" y="{base + 16}" font-size="9" fill="{MUTED}" text-anchor="end">10 kHz</text>')
    return "".join(out)


def checks(items, x0, y, fs, t0, step, gap=22):
    cw, x, out = fs * 0.6, x0, []
    for i, label in enumerate(items):
        out.append(
            f'<g class="f" style="--d:{t0 + i * step:.3f}s"><path d="M{x:.1f} {y - 5:.1f}l3.6 3.8L{x + 11.5:.1f} {y - 11:.1f}" '
            f'fill="none" stroke="{TEAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<text x="{x + 19:.1f}" y="{y}" font-size="{fs}" fill="{MUTED}">{escape(label)}</text></g>'
        )
        x += 19 + len(label) * cw + gap
    return "".join(out)


def banner(variant):
    wide = variant == "wide"
    W, H = (720, 300) if wide else (420, 388)
    pad, fs = (28, 15) if wide else (24, 14)
    cw = fs * 0.6
    Y = dict(A=84, N=128, R=156, B=206, C1=234, C2=258, E=288) if wide else dict(A=82, N=122, R=146, B=186, C1=212, C2=236, E=272)
    fsN, fsR = (38, 17) if wide else (30, 14.5)
    css, p = SPECTRUM_CSS, [window(W, H, "sergio@github: ~"), grid(W, H, "x" if wide else "y")]

    # whoami
    p.append(prompt(pad, Y["A"], fs, .25))
    p.append(typed("whoami", pad + 2 * cw, Y["A"], fs, FG, .55, .065))
    el, c = caret("cA", pad + 2 * cw, Y["A"], fs, 6, .55, .065)
    p.append(el)
    css += c
    p.append(f'<text class="f" style="--d:1.2s" x="{pad}" y="{Y["N"]}" font-size="{fsN}" font-weight="700" fill="{FG}">Sergio Romero</text>')
    p.append(f'<text class="f" style="--d:1.45s" x="{pad}" y="{Y["R"]}" font-size="{fsR}" fill="{TEAL}">Full Stack · IoT · DevSecOps</text>')

    # ./ship --prod
    p.append(prompt(pad, Y["B"], fs, 2.2))
    p.append(typed("./ship --prod", pad + 2 * cw, Y["B"], fs, FG, 2.5, .065))
    el, c = caret("cB", pad + 2 * cw, Y["B"], fs, 13, 2.5, .065)
    p.append(el)
    css += c
    p.append(checks(["interfaz", "api", "datos"], pad, Y["C1"], 13, 3.5, .28))
    p.append(checks(["seguridad", "despliegue", "producción"], pad, Y["C2"], 13, 4.34, .28))

    # prompt final con cursor parpadeante
    p.append(prompt(pad, Y["E"], fs, 5.35))
    p.append(f'<rect class="cF" x="{pad + 2 * cw:.2f}" y="{Y["E"] - fs * .86:.2f}" width="{cw * .9:.2f}" height="{fs * 1.14:.2f}" fill="{TEAL}"/>')
    css += "@keyframes blink{0%,49.9%{opacity:1}50%,100%{opacity:0}}.cF{animation:pop 1ms linear 5.35s backwards,blink 1.1s steps(1,end) 5.35s infinite}"

    # espectro 1/3 de octava
    if wide:
        p.append(spectrum(452, 692, 240, 150, .9))
    else:
        p.append(spectrum(pad, W - pad, 346, 52, .9))
    return svg(
        W, H, "".join(p),
        "Sergio Romero — Full Stack, IoT y DevSecOps",
        "Terminal animada: whoami → Sergio Romero, Full Stack · IoT · DevSecOps; ./ship --prod → interfaz, api, datos, seguridad, despliegue, producción. A la derecha, un espectro de tercios de octava.",
        css,
    )


# ───────────────────────── stack ─────────────────────────
GROUPS = [
    ("languages", ["TypeScript", "JavaScript", "Python", "SQL"]),
    ("frontend", ["Next.js", "React", "React Native", "Tailwind CSS"]),
    ("backend", ["Node.js", "Express", "FastAPI", "PostgreSQL", "MongoDB", "MQTT", "Redis"]),
    ("infra", ["Docker", "Nginx Proxy Manager", "Linux", "GitHub Actions"]),
    ("tools", ["Git", "FlutterFlow", "Supabase", "Playwright"]),
]


DB_ICON = "M12,3C7.58,3 4,4.79 4,7C4,9.21 7.58,11 12,11C16.42,11 20,9.21 20,7C20,4.79 16.42,3 12,3M4,9V12C4,14.21 7.58,16 12,16C16.42,16 20,14.21 20,12V9C20,11.21 16.42,13 12,13C7.58,13 4,11.21 4,9M4,14V17C4,19.21 7.58,21 12,21C16.42,21 20,19.21 20,17V14C20,16.21 16.42,18 12,18C7.58,18 4,16.21 4,14Z"


def chip(name, x, y, icons, fs, off, gap):
    """Icono de marca (simple-icons, CC0) en teal + nombre. Devuelve (svg, ancho incluyendo el hueco)."""
    ic = icons.get(name) or ({"path": DB_ICON} if name == "SQL" else None)
    sc = (fs + 3) / 24  # el icono mide un poco más que el texto
    if ic:
        mark = f'<g transform="translate({x:.1f} {y - fs:.1f}) scale({sc:.4f})"><path d="{ic["path"]}" fill="{TEAL}"/></g>'
    else:  # sin icono de marca: viñeta
        mark = f'<rect x="{x + 3:.1f}" y="{y - fs * .72:.1f}" width="8" height="8" rx="2" fill="{TEAL}" fill-opacity=".55"/>'
    return mark + f'<text x="{x + off:.1f}" y="{y}" font-size="{fs}" fill="{FG}">{escape(name)}</text>', off + len(name) * fs * 0.6 + gap


def stack(variant):
    wide = variant == "wide"
    W = 720 if wide else 420
    pad, row_h = (28, 30) if wide else (24, 26)
    fs, off, gap = (13, 23, 22) if wide else (12, 21, 14)
    icons = json.load(open(os.path.join(HERE, "icons.json")))
    body, y = [], 70
    x_chips = pad + 118 if wide else pad
    for label, names in GROUPS:
        body.append(f'<text x="{pad}" y="{y}" font-size="12" fill="{TEAL}">./{label}</text>')
        if not wide:
            y += row_h - 2
        x = x_chips
        for n in names:
            el, w = chip(n, x, y, icons, fs, off, gap)
            if x + w - gap > W - pad and x != x_chips:  # salto de línea
                x, y = x_chips, y + row_h
                el, w = chip(n, x, y, icons, fs, off, gap)
            body.append(el)
            x += w
        y += row_h + (8 if wide else 12)
    H = y - row_h + 26
    all_items = ", ".join(f"{g}: {', '.join(n)}" for g, n in GROUPS)
    return svg(W, H, window(W, H, "sergio@github: ~/stack") + "".join(body), "Stack", all_items)


# ───────────────────────── stats ─────────────────────────
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
# Marcado/estilos y el andamiaje nativo que React Native genera solo (C++, Objective-C, Kotlin…): no es código propio.
IGNORE_LANGS = {"HTML", "CSS", "SCSS", "Sass", "Less", "Stylus", "Dockerfile", "Shell", "Makefile", "C++", "C", "Objective-C", "Objective-C++", "Kotlin", "CMake", "Ruby", "Logos"}
QUERY = """query($after:String){viewer{login
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
 repositories(first:100 after:$after ownerAffiliations:OWNER isFork:false){pageInfo{hasNextPage endCursor}
  nodes{languages(first:10 orderBy:{field:SIZE direction:DESC}){edges{size node{name}}}}}}}"""


def fetch(token):
    langs, after, cal = {}, None, None
    while True:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": {"after": after}}).encode(),
            headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        if "errors" in d:
            raise SystemExit(f"GraphQL: {d['errors']}")
        v = d["data"]["viewer"]
        cal = cal or v["contributionsCollection"]["contributionCalendar"]
        for repo in v["repositories"]["nodes"]:
            for e in repo["languages"]["edges"]:
                langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
        pi = v["repositories"]["pageInfo"]
        if not pi["hasNextPage"]:
            return cal, langs
        after = pi["endCursor"]


def mix(hex_fg, hex_bg, a):
    f = [int(hex_fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(b[i] + (f[i] - b[i]) * a):02x}" for i in range(3))


def fmt(n):
    return f"{n:,}".replace(",", ".")


def stats(variant, cal, langs, today):
    wide = variant == "wide"
    W, pad = (720, 28) if wide else (420, 24)
    weeks = cal["weeks"] if wide else cal["weeks"][-28:]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    active = sum(1 for _, c in days if c)
    best = max(days, key=lambda t: t[1])
    nz = sorted(c for _, c in days if c)
    cap = max(1, nz[int(len(nz) * .95) - 1] if nz else 1)  # el percentil 95 evita que un día enorme aplane todo
    shades = [mix(TEAL, CARD, a) for a in (.0, .24, .44, .70, 1.0)]
    shades[0] = "#121a29"

    body, y = [], 64
    body.append(f'<text x="{pad}" y="{y}" font-size="13" fill="{TEAL}">$</text><text x="{pad + 18}" y="{y}" font-size="13" fill="{FG}">stats --last-year</text>')
    y += 34
    metrics = [(fmt(cal["totalContributions"]), "contribuciones"), (str(active), "días activos"), (str(best[1]), f"mejor día · {best[0].day} {MESES[best[0].month - 1]}")]
    colw = (W - 2 * pad) / 3
    for i, (v, lab) in enumerate(metrics):
        mx = pad + i * colw
        body.append(f'<text x="{mx:.1f}" y="{y + 22}" font-size="26" font-weight="700" fill="{FG}">{v}</text>')
        body.append(f'<text x="{mx:.1f}" y="{y + 40}" font-size="11" fill="{MUTED}">{escape(lab)}</text>')
    y += 54 + 14

    # mapa de calor
    pitch = (W - 2 * pad) / len(weeks)
    cell = pitch - 2.6
    last_label_x = -99
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            date = dt.date.fromisoformat(d["date"])
            c = d["contributionCount"]
            lvl = 0 if c == 0 else min(4, 1 + int(3.999 * min(c, cap) / cap))
            gx, gy = pad + wi * pitch, y + 14 + ((date.weekday() + 1) % 7) * pitch
            body.append(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2" fill="{shades[lvl]}"/>')
            if date.day <= 7 and ((date.weekday() + 1) % 7) == 0 and gx - last_label_x > 34:
                body.append(f'<text x="{gx:.1f}" y="{y + 8}" font-size="10" fill="{MUTED}">{MESES[date.month - 1]}</text>')
                last_label_x = gx
    y += 14 + 7 * pitch + 12
    # leyenda
    lx = W - pad - (5 * 14 + 80)
    body.append(f'<text x="{lx}" y="{y + 8}" font-size="10" fill="{MUTED}">menos</text>')
    for i, s in enumerate(shades):
        body.append(f'<rect x="{lx + 36 + i * 14}" y="{y}" width="10" height="10" rx="2" fill="{s}"/>')
    body.append(f'<text x="{lx + 36 + 5 * 14 + 2}" y="{y + 8}" font-size="10" fill="{MUTED}">más</text>')
    y += 34

    # lenguajes
    items = sorted(((n, b) for n, b in langs.items() if n not in IGNORE_LANGS), key=lambda t: -t[1])
    tot = sum(b for _, b in items) or 1
    top = items[:5]
    rest = sum(b for _, b in items[5:])
    if rest:
        top.append(("otros", rest))
    alphas = [1, .74, .52, .36, .24, .15]
    x, bw = pad, W - 2 * pad
    body.append(f'<clipPath id="lc"><rect x="{pad}" y="{y}" width="{bw}" height="8" rx="4"/></clipPath><g clip-path="url(#lc)">')
    for i, (n, b) in enumerate(top):
        w = bw * b / tot
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{w + .5:.1f}" height="8" fill="{TEAL}" fill-opacity="{alphas[i]}"/>')
        x += w
    body.append("</g>")
    y += 26
    lx, ly = pad, y
    for i, (n, b) in enumerate(top):
        label = f"{n} {round(100 * b / tot)}%"
        wlab = 14 + len(label) * 6.6 + 16
        if lx + wlab > W - pad:
            lx, ly = pad, ly + 20
        body.append(f'<rect x="{lx}" y="{ly - 8}" width="9" height="9" rx="2.5" fill="{TEAL}" fill-opacity="{alphas[i]}"/>')
        body.append(f'<text x="{lx + 14}" y="{ly}" font-size="11" fill="{MUTED}">{escape(label)}</text>')
        lx += wlab
    H = ly + 30
    body.append(f'<text x="{W - pad}" y="{H - 12}" font-size="10" fill="#4b5873" text-anchor="end">actualizado {today.isoformat()}</text>')
    return svg(
        W, H, window(W, H, "sergio@github: ~/actividad") + "".join(body),
        "Actividad en GitHub",
        f"{cal['totalContributions']} contribuciones en el último año, {active} días activos. Lenguajes: "
        + ", ".join(f"{n} {round(100 * b / tot)}%" for n, b in top),
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {name}  {len(content) / 1024:.1f} KB")


def main(what):
    if what in ("banner", "all"):
        write("banner.svg", banner("wide")), write("banner-m.svg", banner("narrow"))
    if what in ("stack", "all"):
        write("stack.svg", stack("wide")), write("stack-m.svg", stack("narrow"))
    if what in ("stats", "all"):
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("falta GH_TOKEN")
        cal, langs = fetch(token)
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).date()
        write("stats.svg", stats("wide", cal, langs, today)), write("stats-m.svg", stats("narrow", cal, langs, today))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
