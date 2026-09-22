# -*- coding: utf-8 -*-
"""2026-09-22 の見た目の刷新を、サイトの元ファイルに当てる（1回だけ流す）。

参考: Apple（白と #f5f5f7・余白・大きな絵）/ Superlist（霞・ピル）/
      landsolution（漂うグラデーション・小さなループ）/ チケプラTrade（動く帯と動かない地）
決めたこと:
  - 動くのはホーム冒頭の帯（.band）の中だけ。帯の外は白黒。
  - 足す色は2つ: 青（--flag。リンク・今いる場所）と コーラル（--coral。AI だけ）。
  - ライトとダークの両方。bare :root が明るい面、prefers-color-scheme と data-theme で暗い面。
  - フォントは Schibsted Grotesk（英数）+ Zen Kaku Gothic New（日本語）。
  - 上のバーは4つの見出し + その区分のタブの列（.subnav）。降りてくるパネルはやめる。
  - 区画の題は英語を大きく、日本語を小さく添える。
  - ホームの冒頭にバージョンや件数は置かず、ページの最後に置く。
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")


def load(path):
    with io.open(path, encoding="utf-8", newline="") as fp:
        text = fp.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), nl


def save(path, text, nl):
    with io.open(path, "w", encoding="utf-8", newline="") as fp:
        fp.write(text.replace("\n", nl))


def rep(text, old, new, count=1, where=""):
    assert old in text, f"{where}: 見つからない: {old[:70]!r}"
    return text.replace(old, new, count) if count else text.replace(old, new)


# ---------------------------------------------------------------- base.css
TOKENS_LIGHT = """:root {
  --ground: #ffffff;
  --ground-2: #f5f5f7;
  --panel: #ffffff;
  --panel-hi: #f5f5f7;
  --plate: #f5f5f7;

  --wire: #d2d2d7;
  --wire-dim: #e8e8ed;

  --ink: #1d1d1f;
  --ink-mid: #4a4a4f;
  --ink-dim: #86868b;
  --on-ink: #ffffff;
  --ink-hover: #3a3a3f;

  /* 足した2色。青は「進む・今いる場所」、コーラルは AI だけ */
  --flag: #0071e3;
  --flag-hover: #0062c4;
  --flag-soft: rgba(0, 113, 227, 0.12);
  --on-flag: #ffffff;
  --coral: #f2552c;
  --on-coral: #ffffff;

  --fx: #9a4b00;
  --alert: #b3261e;
  --ok: #2f6b3c;
  --warn-bg: #fff8f2;
  --warn-line: #f0ddc9;
  --tag-wait: #f3e4d6;
  --tag-open: #e3edf7;
  --tag-done: #e2efe4;
  --bar-bg: rgba(255, 255, 255, 0.82);

  /* 冒頭の帯（灰色の霞に、青とコーラルをごく薄く） */
  --band: #6f757e;
  --band-1: rgba(214, 219, 226, 0.75);
  --band-2: rgba(58, 66, 78, 0.8);
  --band-3: rgba(160, 168, 180, 0.7);
  --band-blue: rgba(0, 113, 227, 0.26);
  --band-coral: rgba(255, 94, 58, 0.16);
  --band-word: rgba(255, 255, 255, 0.15);
  --card: #ffffff;
  --deck-shadow: 0 24px 60px -24px rgba(0, 0, 0, 0.45);

  --font-display: "Schibsted Grotesk", "Zen Kaku Gothic New", -apple-system, BlinkMacSystemFont,
                  "Hiragino Sans", "Yu Gothic", system-ui, sans-serif;
  --font-body: "Schibsted Grotesk", "Zen Kaku Gothic New", -apple-system, BlinkMacSystemFont,
               "Hiragino Sans", "Yu Gothic", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;

  --shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
  --shadow-lift: 0 12px 34px rgba(0, 0, 0, 0.12);
  --radius: 18px;

  --gutter: 58px;
  --bar: 56px;
  color-scheme: light;
}
"""

DARK_VALUES = """  --ground: #000000;
  --ground-2: #161617;
  --panel: #1c1c1e;
  --panel-hi: #232326;
  --plate: #161617;
  --wire: #3a3a3e;
  --wire-dim: #2a2a2d;
  --ink: #f5f5f7;
  --ink-mid: #c7c7cc;
  --ink-dim: #8e8e93;
  --on-ink: #000000;
  --ink-hover: #d9d9de;
  --flag: #2997ff;
  --flag-hover: #54acff;
  --flag-soft: rgba(41, 151, 255, 0.16);
  --coral: #ff6a45;
  --fx: #f0a35e;
  --alert: #ff6b61;
  --ok: #7dd08f;
  --warn-bg: #2a2118;
  --warn-line: #4a3a28;
  --tag-wait: #3a2c1e;
  --tag-open: #1a2c40;
  --tag-done: #1c3322;
  --bar-bg: rgba(0, 0, 0, 0.72);
  --band: #2b2f35;
  --band-1: rgba(120, 128, 140, 0.55);
  --band-2: rgba(10, 12, 16, 0.85);
  --band-3: rgba(84, 92, 104, 0.6);
  --band-blue: rgba(41, 151, 255, 0.2);
  --band-coral: rgba(255, 106, 69, 0.12);
  --band-word: rgba(255, 255, 255, 0.07);
  --card: #1c1c1e;
  --deck-shadow: 0 24px 60px -20px rgba(0, 0, 0, 0.8);
  --shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
  --shadow-lift: 0 12px 34px rgba(0, 0, 0, 0.6);
  color-scheme: dark;
"""

TOKENS_DARK = ("@media (prefers-color-scheme: dark) {\n  :root:not([data-theme=\"light\"]) {\n"
               + "".join("  " + line + "\n" for line in DARK_VALUES.rstrip("\n").split("\n"))
               + "  }\n}\n:root[data-theme=\"dark\"] {\n" + DARK_VALUES + "}\n")

NEW_CSS = r"""

/* =====================================================================
   2026-09-22 刷新（tools_redesign_2026_09_22.py が足した分）
   ===================================================================== */

body { overflow-x: clip; }

/* ---------- 上のバー: 4つの見出し + その区分のタブの列 ---------- */
.sidenav { background: var(--bar-bg); }
.nav-inner { max-width: 1120px; height: var(--bar); }
.mega { display: none !important; }
.nav-drop > button.nav-tab[aria-expanded="true"],
.nav-drop > a[aria-expanded="true"] { background: none; }
.sidenav .nav-menu { justify-content: center; }
.sidenav .nav-menu > li > a,
.sidenav .nav-menu > li > button.nav-tab {
  font-size: 0.86rem;
  font-weight: 600;
  padding: 9px 15px;
  color: var(--ink-dim);
}
.sidenav .nav-menu > li.is-on > a,
.sidenav .nav-menu > li.is-on > button.nav-tab {
  background: var(--ink);
  color: var(--on-ink);
}
.sidenav .nav-menu > li > a:hover,
.sidenav .nav-menu > li > button.nav-tab:hover { color: var(--ink); }
.sidenav .nav-menu > li.is-on > a:hover,
.sidenav .nav-menu > li.is-on > button.nav-tab:hover { color: var(--on-ink); }

.subnav {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 22px 12px;
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.subnav::-webkit-scrollbar { display: none; }
.subnav[hidden] { display: none; }
.sidenav .subnav a,
.sidenav .subnav button.nav-tab {
  flex: none;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 8px 14px;
  border: 1px solid var(--wire-dim);
  border-radius: 980px;
  color: var(--ink-mid);
  background: var(--ground);
}
.sidenav .subnav a:hover,
.sidenav .subnav button.nav-tab:hover { background: var(--ground-2); color: var(--ink); }
.sidenav .subnav a[aria-current="page"],
.sidenav .subnav button.nav-tab[aria-selected="true"] {
  background: var(--flag);
  border-color: var(--flag);
  color: var(--on-flag);
}
@media (max-width: 720px) {
  .subnav { padding: 0 16px 10px; }
}

/* 明・暗・自動の切り替え（上のバーの右端） */
.theme-switch { display: flex; padding: 3px; border-radius: 980px; background: var(--ground-2); flex: none; }
.theme-switch button {
  border: none; background: none; cursor: pointer;
  font: inherit; font-size: 0.68rem; font-weight: 700;
  color: var(--ink-dim);
  padding: 5px 8px; border-radius: 980px;
}
.theme-switch button[aria-pressed="true"] { background: var(--panel); color: var(--ink); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.16); }
@media (max-width: 900px) { .theme-switch { display: none; } }

/* AI は コーラル */
.nav-beta { background: var(--coral); border-color: var(--coral); color: var(--on-coral); }
.ask-go { background: var(--coral); color: var(--on-coral); }
.ask-go:hover { background: var(--coral); filter: brightness(1.06); }
.chat-send { background: var(--ink); color: var(--on-ink); }

/* ---------- 題: 英語を大きく、日本語を小さく ---------- */
.masthead { display: flex; flex-direction: column; padding-top: 12px; }
.masthead .eyebrow {
  order: 0;
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 6.4vw, 4.2rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--ink);
  margin: 0;
}
.masthead h1 {
  order: 1;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ink-dim);
  margin: 12px 0 16px;
}
.masthead .lede { order: 2; }
.masthead > :not(.eyebrow):not(h1):not(.lede) { order: 3; }

.stage h3 .en {
  display: block;
  font-family: var(--font-display);
  font-size: clamp(1.9rem, 4.6vw, 3rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.02;
  color: var(--ink);
  margin-bottom: 8px;
}
.stage h3:has(.en) { font-size: 0.86rem; font-weight: 700; letter-spacing: 0.02em; color: var(--ink-dim); }

/* ---------- ホーム冒頭の帯（ここだけが動く） ---------- */
.band {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background: var(--band);
  color: #ffffff;
  border-radius: 0 0 clamp(28px, 4.5vw, 48px) clamp(28px, 4.5vw, 48px);
  margin: -40px calc(50% - 50vw) 0;
  padding: clamp(28px, 4vw, 44px) 0 clamp(26px, 3.6vw, 40px);
}
.band-fog { position: absolute; inset: -20%; z-index: -2; pointer-events: none; }
.band-fog i { position: absolute; border-radius: 50%; filter: blur(70px); will-change: transform; }
.band-fog i:nth-child(1) { width: 55%; height: 70%; left: 5%; top: 0; background: var(--band-1); animation: bandf1 18s ease-in-out infinite alternate; }
.band-fog i:nth-child(2) { width: 60%; height: 80%; right: -5%; top: 20%; background: var(--band-2); animation: bandf2 22s ease-in-out infinite alternate; }
.band-fog i:nth-child(3) { width: 45%; height: 55%; left: 30%; bottom: -5%; background: var(--band-3); animation: bandf3 26s ease-in-out infinite alternate; }
.band-fog i:nth-child(4) { width: 38%; height: 50%; right: 8%; top: -10%; background: var(--band-blue); animation: bandf3 24s ease-in-out infinite alternate-reverse; }
.band-fog i:nth-child(5) { width: 30%; height: 42%; left: -6%; bottom: 0; background: var(--band-coral); animation: bandf1 28s ease-in-out infinite alternate-reverse; }
@keyframes bandf1 { to { transform: translate(18%, 14%) scale(1.15); } }
@keyframes bandf2 { to { transform: translate(-16%, -10%) scale(0.9); } }
@keyframes bandf3 { to { transform: translate(-20%, -18%) scale(1.2); } }
.band-word {
  position: absolute; z-index: -1; left: -0.04em; top: clamp(96px, 12vw, 128px);
  font-family: var(--font-display);
  font-size: clamp(4.6rem, 15vw, 12rem); font-weight: 800; letter-spacing: -0.05em; line-height: 0.8;
  color: var(--band-word); white-space: nowrap; pointer-events: none; user-select: none;
}
.band-inner { max-width: 1120px; margin: 0 auto; padding: 0 22px; }
.band-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 3.6vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.15;
  color: #ffffff;
  text-align: left;
}
.band-lede { margin: 8px 0 0; max-width: 36em; font-size: 0.95rem; line-height: 1.7; color: rgba(255, 255, 255, 0.82); }

.band-search {
  margin-top: 20px;
  max-width: 760px;
  display: flex; align-items: center; gap: 8px;
  background: #ffffff; color: #1d1d1f;
  border-radius: 980px;
  padding: 7px 7px 7px 24px;
  box-shadow: 0 12px 40px -18px rgba(0, 0, 0, 0.55);
}
.band-search input {
  flex: 1; min-width: 0;
  border: none; outline: none; background: none;
  font: inherit; font-size: 1.02rem; font-weight: 500;
  color: #1d1d1f; padding: 12px 0;
}
.band-search input::placeholder { color: #8e8e93; }
.band-go {
  flex: none;
  display: inline-flex; align-items: center; gap: 6px;
  border: none; border-radius: 980px; cursor: pointer;
  font: inherit; font-size: 0.84rem; font-weight: 700;
  padding: 11px 16px;
}
.band-go svg { width: 16px; height: 16px; display: block; }
.band-go--find { background: #f2f2f4; color: #1d1d1f; }
.band-go--find:hover { background: #e6e6ea; }
.band-go--ai { background: var(--coral); color: var(--on-coral); }
.band-go--ai:hover { filter: brightness(1.06); }
.band-go--ai small { font-size: 0.6rem; opacity: 0.8; }
.band-go[hidden] { display: none; }

/* 重なったカード（新着の実験） */
.deck { position: relative; height: clamp(372px, 40vw, 430px); margin-top: clamp(26px, 3.4vw, 36px); }
.deck-card {
  position: absolute; left: 50%; top: 0;
  width: min(340px, 76vw);
  border-radius: 28px;
  background: var(--card); color: var(--ink);
  padding: 10px 10px 18px;
  box-shadow: var(--deck-shadow);
  text-decoration: none;
  transform-origin: 50% 90%;
  transition: transform 0.6s cubic-bezier(.2,.7,.2,1), opacity 0.6s;
}
.deck-card img { width: 100%; aspect-ratio: 16 / 11; object-fit: cover; border-radius: 20px; display: block; background: #2a2a2e; }
.deck-card .deck-meta { display: block; margin: 14px 10px 0; font-size: 0.74rem; font-weight: 700; color: var(--flag); }
.deck-card .deck-t { display: block; margin: 4px 10px 0; font-family: var(--font-display); font-size: 1.06rem; line-height: 1.45; font-weight: 800; letter-spacing: -0.01em; }
.deck-card .deck-d { display: block; margin: 6px 10px 0; font-size: 0.8rem; line-height: 1.6; color: var(--ink-mid); }
.deck-ctrl { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.deck-play { width: 44px; height: 44px; border-radius: 50%; border: none; display: grid; place-items: center; cursor: pointer; background: #ffffff; color: #1d1d1f; flex: none; }
.deck-play svg, .deck-arrow svg { width: 18px; height: 18px; display: block; }
.deck-arrow { width: 40px; height: 40px; border: none; background: none; color: #ffffff; cursor: pointer; display: grid; place-items: center; border-radius: 50%; }
.deck-arrow:hover { background: rgba(255, 255, 255, 0.12); }
.deck-dots { display: flex; gap: 8px; align-items: center; margin-inline: auto; }
.deck-dots button { width: 9px; height: 9px; padding: 0; border: none; border-radius: 980px; background: rgba(255, 255, 255, 0.4); cursor: pointer; transition: width 0.35s, background 0.35s; }
.deck-dots button[aria-current="true"] { width: 34px; background: var(--flag); }

@media (max-width: 720px) {
  .band { margin-top: -28px; }
  .band-inner { padding: 0 16px; }
  .band-search { padding-left: 18px; }
  .band-go--find { display: none; }
  .deck { height: 392px; }
}

/* ホームの最後: この場所の数字と環境（冒頭からここへ移した） */
.site-facts {
  margin-top: clamp(72px, 9vw, 112px);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--wire-dim);
  border-bottom: 1px solid var(--wire-dim);
}
.site-facts a {
  display: block;
  text-decoration: none;
  color: var(--ink);
  padding: 22px clamp(12px, 2.2vw, 24px);
  border-right: 1px solid var(--wire-dim);
  transition: background 0.2s;
}
.site-facts a:last-child { border-right: none; }
.site-facts a:hover { background: var(--ground-2); }
.site-facts b { display: block; font-family: var(--font-display); font-size: clamp(1.7rem, 3.2vw, 2.4rem); font-weight: 800; letter-spacing: -0.035em; line-height: 1; font-variant-numeric: tabular-nums; }
.site-facts span { display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.8rem; font-weight: 700; color: var(--ink-mid); }
.site-facts em { font-style: normal; font-size: 0.64rem; letter-spacing: 0.06em; color: var(--ink-dim); }
.site-env { margin: 14px 0 0; font-size: 0.76rem; color: var(--ink-dim); }
@media (max-width: 720px) {
  .site-facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .site-facts a:nth-child(2) { border-right: none; }
  .site-facts a:nth-child(-n+2) { border-bottom: 1px solid var(--wire-dim); }
}

@media (prefers-reduced-motion: reduce) {
  .band-fog i { animation: none; }
  .deck-card, .deck-dots button { transition: none; }
}
"""


def fix_css():
    path = os.path.join(SITE, "base.css")
    css, nl = load(path)
    start = css.index(":root {")
    end = css.index("}\n", start) + 2
    css = css[:start] + TOKENS_LIGHT + TOKENS_DARK + css[end:]

    # 白抜き文字: 地が青なら --on-flag、それ以外（地が --ink）は --on-ink
    out, pos = [], 0
    for m in re.finditer(r"[^{}]*\{[^{}]*\}", css):
        block = m.group(0)
        if "color: #ffffff" in block and ":root" not in block:
            key = "var(--on-flag)" if "background: var(--flag)" in block else "var(--on-ink)"
            block = block.replace("color: #ffffff", "color: " + key)
        out.append(css[pos:m.start()] + block)
        pos = m.end()
    out.append(css[pos:])
    css = "".join(out)

    pairs = [
        ("background: rgba(255, 255, 255, 0.82);", "background: var(--bar-bg);"),
        (".tagchip.is-on span { color: rgba(255, 255, 255, 0.7); }", ".tagchip.is-on span { color: var(--on-ink); opacity: 0.7; }"),
        ("background: #fff8f2;", "background: var(--warn-bg);"),
        ("border: 1px solid #f0ddc9;", "border: 1px solid var(--warn-line);"),
        ("background: #0055aa;", "background: var(--flag-hover);"),
        ("background: #3a3a3f;", "background: var(--ink-hover);"),
        (".queue--wait .queue-tag { background: #f3e4d6;", ".queue--wait .queue-tag { background: var(--tag-wait);"),
        (".queue--open .queue-tag { background: #e3edf7;", ".queue--open .queue-tag { background: var(--tag-open);"),
        (".queue--done .queue-tag { background: #e2efe4; color: #2f6b3c; }", ".queue--done .queue-tag { background: var(--tag-done); color: var(--ok); }"),
        ("box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.14);", "box-shadow: 0 0 0 3px var(--flag-soft);"),
        ("background: rgba(255, 255, 255, 0.86);", "background: var(--bar-bg);"),
        (".tile-go--guide:hover { background: #0055aa; border-color: #0055aa; }", ".tile-go--guide:hover { background: var(--flag-hover); border-color: var(--flag-hover); }"),
    ]
    for old, new in pairs:
        if old in css:
            css = css.replace(old, new)
    if "2026-09-22 刷新" not in css:
        css = css.rstrip("\n") + "\n" + NEW_CSS
    save(path, css, nl)


# ---------------------------------------------------------------- templates
FONT_OLD = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?[^"]*">')
FONT_NEW = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800'
            '&family=Zen+Kaku+Gothic+New:wght@400;500;700;900&family=JetBrains+Mono:wght@400;500&display=swap">')

EYEBROWS = {
    "home_template.html": [("<p class=\"eyebrow\">How to</p>", "<p class=\"eyebrow\">Practice</p>"),
                           ("<p class=\"eyebrow\">Commissions</p>", "<p class=\"eyebrow\">Works</p>"),
                           ("<p class=\"eyebrow\">Terminology</p>", "<p class=\"eyebrow\">Glossary</p>"),
                           ("<h1>重くしないために</h1>", "<h1>効率化</h1>")],
    "glossary_template.html": [("<p class=\"eyebrow\">Houdini terminology for beginners</p>", "<p class=\"eyebrow\">Glossary</p>")],
    "links_template.html": [("<p class=\"eyebrow\">References &amp; learning material</p>", "<p class=\"eyebrow\">References</p>")],
    "log_fx_template.html": [("<p class=\"eyebrow\">FX &amp; Simulation / hython 21.0.700</p>", "<p class=\"eyebrow\">Effects Log</p>")],
    "log_pm_template.html": [("<p class=\"eyebrow\">Procedural Modeling / hython 21.0.700</p>", "<p class=\"eyebrow\">Modeling Log</p>")],
}

STAGE_EN = [
    ("<h3>はじめての人へ</h3>", '<h3><span class="en">Start Here</span>はじめての人へ</h3>'),
    ("<h3>これまでに作ったもの</h3>", '<h3><span class="en">Showcase</span>これまでに作ったもの</h3>'),
    ("<h3>やり方</h3>", '<h3><span class="en">Workflow</span>やり方</h3>'),
    ("<h3>この場所の決めごと</h3>", '<h3><span class="en">Rules</span>この場所の決めごと</h3>'),
    ("<h3>使っている道具</h3>", '<h3><span class="en">Tools</span>使っている道具</h3>'),
]

HERO_OLD_START = '      <header class="hero">'
HERO_NEW = """      <div class="band">
        <div class="band-fog" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
        <div class="band-word" aria-hidden="true">Houdini Lab</div>
        <div class="band-inner">
          <h1 class="band-title">Houdini 研究部</h1>
          <p class="band-lede">Houdini の機能を1つずつ動かし、結果を数値で記録しています。実験の記録、作り方の手順、ノードと用語の解説を、ここから探せます。</p>
          <form class="band-search" id="band-search" role="search" onsubmit="return false">
            <input type="search" id="band-q" placeholder="何をお探しですか？" autocomplete="off"
                   aria-label="探す言葉、または AI への質問">
            <button type="submit" class="band-go band-go--find" id="band-find">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="2"/><path d="M15.4 15.4L20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>探す
            </button>
            <button type="button" class="band-go band-go--ai" id="band-ai" hidden>
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.5l1.9 4.9 4.9 1.9-4.9 1.9L12 17.1l-1.9-4.9-4.9-1.9 4.9-1.9z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>AI に聞く <small>Beta</small>
            </button>
          </form>
<!--DECK-->
        </div>
      </div>
"""

FACTS_END = """
      <nav class="site-facts" aria-label="この場所の数字">
        <a href="<!--URL_EXPERIMENTS-->"><b><!--EXP_COUNT--></b><span>実験ログ<em>EXPERIMENTS</em></span></a>
        <a href="<!--URL_GUIDES-->"><b><!--GUIDE_COUNT--></b><span>実践ガイド<em>PRACTICE</em></span></a>
        <a href="<!--URL_NODES-->"><b><!--NODE_COUNT--></b><span>ノード解説<em>NODES</em></span></a>
        <a href="<!--URL_GLOSSARY-->"><b><!--TERM_COUNT--></b><span>用語集<em>GLOSSARY</em></span></a>
      </nav>
      <p class="site-env">Houdini 21.0.700（Apprentice）· hython で実行 · Gemini Notebook のソース 41 / 300</p>
"""


def fix_templates():
    for name in os.listdir(SITE):
        if not name.endswith("_template.html"):
            continue
        path = os.path.join(SITE, name)
        text, nl = load(path)
        text = FONT_OLD.sub(FONT_NEW, text, count=1)
        for old, new in EYEBROWS.get(name, []):
            if old in text:
                text = text.replace(old, new)
        if name == "home_template.html":
            if HERO_OLD_START in text:
                start = text.index(HERO_OLD_START)
                end = text.index("<!--STRIP-->", start) + len("<!--STRIP-->\n")
                text = text[:start] + HERO_NEW + text[end:]
            for old, new in STAGE_EN:
                if old in text:
                    text = text.replace(old, new)
            anchor = "    </section>\n\n    <!-- ========== 手順 ========== -->"
            if "site-facts" not in text:
                text = rep(text, anchor, FACTS_END + anchor, where=name)
        save(path, text, nl)


# ---------------------------------------------------------------- build_site.py
NAV_OLD = '''    for index, (head, target, columns) in enumerate(MENU):
        current = ' aria-current="page"' if ACTIVE_OF.get(active) == head else ""
        if not columns:
            out.append("        <li>")'''
NAV_NEW = '''    for index, (head, target, columns) in enumerate(MENU):
        current = ' aria-current="page"' if ACTIVE_OF.get(active) == head else ""
        if not columns:
            out.append(f'        <li data-g="{index}">')'''
NAV_OLD2 = '''        out.append('        <li class="nav-drop">')'''
NAV_NEW2 = '''        out.append(f'        <li class="nav-drop" data-g="{index}">')'''
NAV_OLD3 = '''    out.append(f'        <li><a href="{NOTEBOOK_URL}" class="nav-ext"'
               ' target="_blank" rel="noopener noreferrer">Notebook</a></li>')
    out.append("      </ul>")'''
NAV_NEW3 = '''    out.append("      </ul>")
    out.append(THEME_SWITCH)'''
NAV_OLD4 = '''               + BURGER_SVG + "</button>")
    out.append("    </div>")
    out.append("  </nav>")
    return "\\n".join(out)'''
NAV_NEW4 = '''               + BURGER_SVG + "</button>")
    out.append("    </div>")
    # その区分のタブの列。いま居る区分の列だけを出す（どれを出すかは partial_chrome の JS）。
    # 降りてくるパネルの代わり。行き先は MENU の束をそのまま横に並べたもの（2026-09-22）
    for index, (head, target, columns) in enumerate(MENU):
        if not columns:
            continue
        out.append(f'    <div class="subnav" data-g="{index}" hidden>')
        for _col_head, links in columns:
            for child_target, child_label, note in links:
                out.append("      " + control(child_target, child_label,
                                              f' title="{html.escape(note)}"', ident=False))
        out.append("    </div>")
    out.append("  </nav>")
    return "\\n".join(out)'''
CTRL_OLD = '''    def control(target, label, extra=""):
        """行き先ひとつ。ハブではタブの切り替え、それ以外はリンクになる。"""'''
CTRL_NEW = '''    def control(target, label, extra="", ident=True):
        """行き先ひとつ。ハブではタブの切り替え、それ以外はリンクになる。
        ident=False は下のタブの列用（同じ id を2つ作らない）。"""'''
CTRL_OLD2 = '''            return (f'<button type="button" class="nav-tab" role="tab"'
                    f' id="tab-{target}" data-panel="{target}"'
                    f' aria-controls="panel-{target}"'
                    f' aria-selected="false"{extra}>{html.escape(label)}</button>')'''
CTRL_NEW2 = '''            tab_id = f' id="tab-{target}"' if ident else ""
            return (f'<button type="button" class="nav-tab" role="tab"'
                    f'{tab_id} data-panel="{target}"'
                    f' aria-controls="panel-{target}"'
                    f' aria-selected="false"{extra}>{html.escape(label)}</button>')'''
CTRL_OLD3 = '''        if target.startswith("@"):
            href = urls[target[1:]]
            return f'<a href="{href}"{extra}>{html.escape(label)}</a>\''''
CTRL_NEW3 = '''        if target.startswith("@"):
            href = urls[target[1:]]
            here = ' aria-current="page"' if (not ident and target[1:] == active) else ""
            return f'<a href="{href}"{extra}{here}>{html.escape(label)}</a>\''''

THEME = '''
THEME_SWITCH = ('      <div class="theme-switch" role="group" aria-label="表示の明るさ">'
                '<button type="button" data-theme-set="system" aria-pressed="true">自動</button>'
                '<button type="button" data-theme-set="light" aria-pressed="false">明</button>'
                '<button type="button" data-theme-set="dark" aria-pressed="false">暗</button></div>')


def render_deck(urls, count=8):
    """ホームの帯に重ねて出す、新着の実験のカード。押すとその実験の記事へ。"""
    items = list(reversed(DONE[-count:]))
    out = ['          <div class="deck" id="deck" aria-roledescription="カルーセル" aria-label="新着の実験">']
    for d in items:
        href = f'{urls[d["log"]]}#{d["anchor"]}'
        edition = "エフェクト編" if d["log"] == "log_fx" else "モデリング編"
        thumb = d.get("thumb") or ""
        thumb = f"thumb_{d['no']}.png" if os.path.exists(os.path.join(SITE, f"thumb_{d['no']}.png")) else thumb
        out.append(f'            <a class="deck-card" href="{href}">'
                   f'<img src="{thumb}" alt="" loading="lazy" decoding="async">'
                   f'<span class="deck-meta">実験{d["no"]} · {edition}</span>'
                   f'<span class="deck-t">{html.escape(d["title"].split(" — ")[0])}</span>'
                   f'<span class="deck-d">{html.escape(d.get("note", ""))}</span></a>')
    out.append("          </div>")
    out.append('          <div class="deck-ctrl">'
               '<button type="button" class="deck-play" id="deck-play" aria-label="自動の切り替えを止める"></button>'
               '<button type="button" class="deck-arrow" id="deck-prev" aria-label="前の実験">'
               '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
               '<div class="deck-dots" id="deck-dots"></div>'
               '<button type="button" class="deck-arrow" id="deck-next" aria-label="次の実験">'
               '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
               '</div>')
    return "\\n".join(out)

'''


def fix_build():
    path = os.path.join(HERE, "build_site.py")
    text, nl = load(path)
    if "def render_deck" in text:
        print("build_site.py はもう当ててある")
        return
    for old, new in [(NAV_OLD, NAV_NEW), (NAV_OLD2, NAV_NEW2), (NAV_OLD3, NAV_NEW3), (NAV_OLD4, NAV_NEW4),
                     (CTRL_OLD, CTRL_NEW), (CTRL_OLD2, CTRL_NEW2), (CTRL_OLD3, CTRL_NEW3)]:
        text = rep(text, old, new, where="build_site.py")
    text = rep(text, "\ndef render_nav(", THEME + "\ndef render_nav(", where="build_site.py")
    text = rep(text, '        ("<!--STRIP-->", render_strip(guides, urls)),',
               '        ("<!--STRIP-->", render_strip(guides, urls)),\n'
               '        ("<!--DECK-->", render_deck(urls)),\n'
               '        ("<!--GUIDE_COUNT-->", str(len(guides["guides"]))),', where="build_site.py")
    save(path, text, nl)


if __name__ == "__main__":
    fix_css()
    fix_templates()
    fix_build()
    print("当てた")
