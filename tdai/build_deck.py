#!/usr/bin/env python3
"""Agent memory + cross-agent stack deck — GEANT4-deck visual style.
Dark navy theme, cyan/green/amber accents, card layout, 16pt floor on body text.
Covers: TDAI/Falda memory, Sibline bus, UMP, harness integration.
Palette copied verbatim from scripts/build_geant4dna_deck.py per Rick (2026-06-23)."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---- palette (GEANT4 deck) ----
DARK   = RGBColor(0x12, 0x1B, 0x2E)   # deep navy bg
CARD   = RGBColor(0x1B, 0x27, 0x40)   # card fill
ACCENT = RGBColor(0x2E, 0x9E, 0xC9)   # cyan
ACCENT2= RGBColor(0x5B, 0xC8, 0x8A)   # green
WARN   = RGBColor(0xE0, 0x8A, 0x3C)   # amber
PURPLE = RGBColor(0x9B, 0x8C, 0xE0)   # soft violet (cross-agent)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT  = RGBColor(0xD7, 0xE1, 0xEE)
GREY   = RGBColor(0x8A, 0x97, 0xA8)

SW, SH = Inches(13.333), Inches(7.5)
prs = Presentation(); prs.slide_width = SW; prs.slide_height = SH
BLANK = prs.slide_layouts[6]


def bg(slide, color=DARK):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = color


def box(slide, l, t, w, h, fill=None, line=None, line_w=None):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sp.shadow.inherit = False
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = line_w or Pt(1)
    return sp


def txt(slide, l, t, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(l, t, w, h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    first = True
    for line in runs:
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.alignment = line.get("align", align)
        if "space_after" in line: p.space_after = Pt(line["space_after"])
        if "space_before" in line: p.space_before = Pt(line["space_before"])
        segs = line["segs"] if "segs" in line else [line]
        for seg in segs:
            r = p.add_run(); r.text = seg["t"]; f = r.font
            f.size = Pt(seg.get("sz", 18)); f.bold = seg.get("b", False)
            f.italic = seg.get("i", False); f.name = seg.get("font", "Calibri")
            f.color.rgb = seg.get("c", LIGHT)
    return tb


def accent_bar(slide, color=ACCENT, t=Inches(1.18)):
    box(slide, Inches(0.7), t, Inches(2.2), Pt(3), fill=color)

def kicker(slide, text, color=ACCENT):
    txt(slide, Inches(0.7), Inches(0.45), Inches(11), Inches(0.4),
        [{"t": text.upper(), "sz": 14, "b": True, "c": color, "font": "Consolas"}])

def title(slide, text, sz=33):
    txt(slide, Inches(0.7), Inches(0.66), Inches(12), Inches(0.85),
        [{"t": text, "sz": sz, "b": True, "c": WHITE}])

def footer(slide, n, total=16):
    txt(slide, Inches(0.7), Inches(7.08), Inches(9), Inches(0.32),
        [{"t": "Agent memory + cross-agent stack · TDAI / Falda · Sibline · UMP",
          "sz": 9, "c": GREY, "font": "Consolas"}])
    txt(slide, Inches(11.7), Inches(7.08), Inches(1.3), Inches(0.32),
        [{"t": f"{n:02d}/{total}", "sz": 9, "c": GREY, "font": "Consolas",
          "align": PP_ALIGN.RIGHT}], align=PP_ALIGN.RIGHT)

def s_new():
    s = prs.slides.add_slide(BLANK); bg(s); return s

def chip(slide, l, t, w, label, col):
    box(slide, l, t, w, Inches(0.55), fill=col)
    txt(slide, l, t, w, Inches(0.55), [{"t": label, "sz": 16, "b": True, "c": DARK,
        "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def card(slide, l, t, w, h, head, body, col, head_sz=20, body_sz=16):
    box(slide, l, t, w, h, fill=CARD)
    box(slide, l, t, w, Pt(5), fill=col)
    txt(slide, l+Inches(0.22), t+Inches(0.22), w-Inches(0.44), Inches(0.7),
        [{"t": head, "sz": head_sz, "b": True, "c": WHITE}])
    txt(slide, l+Inches(0.22), t+Inches(0.95), w-Inches(0.44), h-Inches(1.1),
        [{"t": body, "sz": body_sz, "c": LIGHT}])

def arrow(slide, l, t, w=Inches(0.45), col=GREY):
    txt(slide, l, t, w, Inches(0.5), [{"t": "\u2192", "sz": 26, "b": True, "c": col,
        "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def darrow(slide, l, t, col=GREY):
    txt(slide, l, t, Inches(0.5), Inches(0.4), [{"t": "\u2193", "sz": 22, "b": True,
        "c": col, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)


# ============ 1 TITLE ============
s = s_new()
box(s, 0, 0, Inches(0.28), SH, fill=ACCENT)
box(s, Inches(0.28), 0, Inches(0.06), SH, fill=ACCENT2)
txt(s, Inches(0.9), Inches(0.7), Inches(11), Inches(0.4),
    [{"t": "AGENT INFRASTRUCTURE · KUKLA + OLLIE", "sz": 14, "b": True, "c": ACCENT, "font": "Consolas"}])
txt(s, Inches(0.9), Inches(2.2), Inches(11.8), Inches(2.4),
    [{"t": "Agent Memory &", "sz": 52, "b": True, "c": WHITE, "space_after": 2},
     {"t": "Cross-Agent Stack", "sz": 52, "b": True, "c": WHITE, "space_after": 8},
     {"t": "How the two-agent family is actually wired", "sz": 23, "c": LIGHT}])
box(s, Inches(0.92), Inches(4.6), Inches(3.0), Pt(3), fill=ACCENT2)
txt(s, Inches(0.9), Inches(4.85), Inches(11.7), Inches(1.2),
    [{"segs": [
        {"t": "Memory  ", "sz": 17, "b": True, "c": ACCENT2},
        {"t": "(TDAI \u2192 Falda \u00b7 UMP)   ", "sz": 16, "c": LIGHT},
        {"t": "Bus  ", "sz": 17, "b": True, "c": ACCENT},
        {"t": "(Sibline)   ", "sz": 16, "c": LIGHT},
        {"t": "Integration  ", "sz": 17, "b": True, "c": WARN},
        {"t": "(harness)", "sz": 16, "c": LIGHT}]}])
txt(s, Inches(0.9), Inches(6.7), Inches(11), Inches(0.4),
    [{"t": "Prepared for Rick Stevens · Argonne · 2026-06-23", "sz": 11, "c": GREY, "font": "Consolas"}])

# ============ 2 TL;DR ============
s = s_new(); kicker(s, "In one look", ACCENT2); accent_bar(s, ACCENT2)
title(s, "The whole stack, in three parts")
cards = [
    ("MEMORY", "Layered per-agent memory (T0\u2192T3). Falda is the born-clean US-origin four-tier engine becoming the primary, migrated from the older TDAI runtime. UMP + vault hold shared facts.", ACCENT),
    ("BUS", "Sibline \u2014 a NATS/JetStream broker \u2014 carries realtime agent\u2194agent messages. One stable v1 subject contract, both directions symmetric.", ACCENT2),
    ("INTEGRATION", "A documented, replication-grade recipe plugs either harness (Hermes / OpenClaw) into Falda \u2014 stand it up + verify from scratch.", WARN),
]
x = Inches(0.7); w = Inches(3.85); gap = Inches(0.18)
for i,(h,b,col) in enumerate(cards):
    card(s, x+i*(w+gap), Inches(1.75), w, Inches(3.5), h, b, col, head_sz=22, body_sz=16)
txt(s, Inches(0.7), Inches(5.55), Inches(12), Inches(1.2),
    [{"segs":[{"t":"Bottom line:  ","sz":17,"b":True,"c":ACCENT2},
      {"t":"two agents, one human, separate identities \u2014 sharing memory and a realtime bus, with the whole thing reproducible from documented templates.","sz":17,"c":LIGHT}]}])
footer(s, 2)

# ============ 3 TWO-AGENT FAMILY ============
s = s_new(); kicker(s, "Cross-agent", PURPLE); accent_bar(s, PURPLE)
title(s, "Two agents, one family")
card(s, Inches(0.7), Inches(1.8), Inches(5.55), Inches(3.6), "KUKLA",
     "Harness: Hermes (Python)\nHost: m1-mac-mini\nRuns the Sibline broker\n@Rick_KuklaBot", PURPLE, body_sz=18)
card(s, Inches(7.08), Inches(1.8), Inches(5.55), Inches(3.6), "OLLIE",
     "Harness: OpenClaw (Node/TS)\nHost: CherryRd\nRuns Falda gateway + tap\n@RickOllie_bot", ACCENT, body_sz=18)
chip(s, Inches(5.55), Inches(3.35), Inches(2.2), "ONE HUMAN: RICK", ACCENT2)
txt(s, Inches(0.7), Inches(5.7), Inches(12), Inches(1.0),
    [{"segs":[{"t":"Shared substrate:  ","sz":16,"b":True,"c":ACCENT},
      {"t":"same model backend (Argo \u2192 Claude). Separate identities \u2014 never impersonate, never speak as a merged agent.","sz":16,"c":LIGHT}]}])
footer(s, 3)

# ============ 4 FIVE MEMORY SYSTEMS ============
s = s_new(); kicker(s, "Memory", ACCENT2); accent_bar(s, ACCENT2)
title(s, "Five memory systems, five jobs")
rows = [
    ("Native (Hermes / OpenClaw)", "per-agent working memory, injected every turn", "PRIVATE", GREY),
    ("Memory vault", "shared cold tier \u2014 markdown cards, read on demand", "SHARED", ACCENT),
    ("UMP", "shared structured store \u2014 36k MCP-exposed cards", "SHARED", PURPLE),
    ("Falda  (T0\u2192T3)", "born-clean US four-tier engine \u2014 becoming primary", "PRIMARY", ACCENT2),
    ("TDAI  (L0\u2192L3)", "legacy live runtime \u2014 migrating from", "RETIRING", WARN),
]
y = Inches(1.8)
for name, job, tag, col in rows:
    box(s, Inches(0.7), y, Inches(12.0), Inches(0.86), fill=CARD)
    box(s, Inches(0.7), y, Pt(5), Inches(0.86), fill=col)
    txt(s, Inches(1.0), y+Inches(0.13), Inches(4.3), Inches(0.6),
        [{"t": name, "sz": 18, "b": True, "c": WHITE}])
    txt(s, Inches(5.3), y+Inches(0.16), Inches(5.0), Inches(0.55),
        [{"t": job, "sz": 16, "c": LIGHT}])
    chip(s, Inches(10.5), y+Inches(0.18), Inches(2.0), tag, col)
    y += Inches(1.0)
footer(s, 4)

# ============ 5 TDAI L0->L3 ============
s = s_new(); kicker(s, "Memory · TDAI (legacy)", ACCENT2); accent_bar(s, ACCENT2)
title(s, "TDAI: the four-layer pipeline (migrating from)")
stages = [
    ("L0", "Stream", "every turn\ncaptured raw", GREY),
    ("L1", "Atoms", "LLM-extracted\nfacts / prefs / rules", ACCENT),
    ("L2", "Scenes", "synthesized\ntopic summaries", ACCENT2),
    ("L3", "Core", "persona\nrollup", WARN),
]
x = Inches(0.7); w = Inches(2.75); gap = Inches(0.45); t = Inches(2.0); h = Inches(2.7)
for i,(tag,name,body,col) in enumerate(stages):
    lx = x+i*(w+gap)
    box(s, lx, t, w, h, fill=CARD); box(s, lx, t, w, Pt(5), fill=col)
    txt(s, lx+Inches(0.2), t+Inches(0.22), w-Inches(0.4), Inches(0.4),
        [{"t": tag, "sz": 16, "b": True, "c": col, "font": "Consolas"}])
    txt(s, lx+Inches(0.2), t+Inches(0.6), w-Inches(0.4), Inches(0.5),
        [{"t": name, "sz": 21, "b": True, "c": WHITE}])
    txt(s, lx+Inches(0.2), t+Inches(1.25), w-Inches(0.4), Inches(1.3),
        [{"t": body, "sz": 16, "c": LIGHT}])
    if i<3: arrow(s, lx+w+Inches(0.04), t+Inches(1.1))
txt(s, Inches(0.7), Inches(5.25), Inches(12), Inches(1.3),
    [{"segs":[{"t":"Distiller","sz":16,"b":True,"c":ACCENT2},
      {"t":" walks L0\u2192L3 on free Argo LLMs. Storage = SQLite + FTS5 + sqlite-vec. ","sz":16,"c":LIGHT},
      {"t":"The reference design","sz":16,"b":True,"c":ACCENT2},
      {"t":" \u2014 the Falda engine inherits its tier model and ships the go-forward implementation.","sz":16,"c":LIGHT}]}])
footer(s, 5)

# ============ 6 FALDA PRIMARY ============
s = s_new(); kicker(s, "Memory · Falda", ACCENT2); accent_bar(s, ACCENT2)
title(s, "Falda: the born-clean US-origin engine")
card(s, Inches(0.7), Inches(1.8), Inches(5.85), Inches(3.5), "What it is",
     "Apache-2.0, US-origin reimplementation of the four-tier model (T0\u2192T3 = Stream / Atoms / Scenes / Core).\nbetter-sqlite3 + sqlite-vec + FTS5.\nHTTP gateway on :8077.\nPublic repo: github.com/rick-stevens-ai/falda.", ACCENT, body_sz=17)
card(s, Inches(6.85), Inches(1.8), Inches(5.78), Inches(3.5), "Why it's the go-forward",
     "Clean-room provenance (no carried-over code).\nSame tier semantics as TDAI \u2014 drop-in upgrade path.\nBecoming the primary memory provider; TDAI is the predecessor being migrated from.\nDual-run during cutover keeps risk low.", ACCENT2, body_sz=17)
txt(s, Inches(0.7), Inches(5.6), Inches(12), Inches(1.1),
    [{"segs":[{"t":"Cutover model:  ","sz":16,"b":True,"c":ACCENT2},
      {"t":"run both engines side-by-side, then flip the memory provider to Falda \u2014 no risky big-bang switch.","sz":16,"c":LIGHT}]}])
footer(s, 6)

# ============ 7 UMP ============
s = s_new(); kicker(s, "Memory · UMP", PURPLE); accent_bar(s, PURPLE)
title(s, "UMP: the shared structured store")
card(s, Inches(0.7), Inches(1.8), Inches(5.85), Inches(3.5), "What it holds",
     "36k+ markdown cards, Dropbox-synced.\nShared across both agents.\nMCP-exposed for structured recall.\nOperator-keyed DID (shared, not per-agent).", PURPLE, body_sz=17)
card(s, Inches(6.85), Inches(1.8), Inches(5.78), Inches(3.5), "The one gotcha",
     "Cards are PRIVATE \u2014 recall MUST pass scope.owner.\nForgetting it = empty results (the dominant failure).\nAlways scope the query to the operator.", WARN, body_sz=17)
txt(s, Inches(0.7), Inches(5.6), Inches(12), Inches(1.1),
    [{"segs":[{"t":"Role:  ","sz":16,"b":True,"c":PURPLE},
      {"t":"shared, durable, structured facts both agents contribute to and read on demand \u2014 the cross-agent knowledge base.","sz":16,"c":LIGHT}]}])
footer(s, 7)

# ============ 8 MEMORY LANDSCAPE (primary vs shared vs legacy) ============
s = s_new(); kicker(s, "Memory", ACCENT); accent_bar(s)
title(s, "Primary vs. shared vs. legacy")
groups = [
    ("PRIMARY", "go-forward recall path", ["Native per-agent", "Falda (T0\u2192T3)"], ACCENT2),
    ("SHARED", "read on demand", ["Memory vault", "UMP (36k cards)"], PURPLE),
    ("LEGACY", "migrating from", ["TDAI (L0\u2192L3)"], WARN),
]
x = Inches(0.7); w = Inches(3.85); gap = Inches(0.18); t = Inches(1.8); h = Inches(3.7)
for i,(head,sub,items,col) in enumerate(groups):
    lx = x+i*(w+gap)
    box(s, lx, t, w, h, fill=CARD); box(s, lx, t, w, Pt(5), fill=col)
    txt(s, lx+Inches(0.22), t+Inches(0.22), w-Inches(0.44), Inches(0.5),
        [{"t": head, "sz": 19, "b": True, "c": col}])
    txt(s, lx+Inches(0.22), t+Inches(0.72), w-Inches(0.44), Inches(0.45),
        [{"t": sub, "sz": 16, "i": True, "c": GREY}])
    txt(s, lx+Inches(0.22), t+Inches(1.3), w-Inches(0.44), Inches(2.2),
        [{"t": "\u2022  "+it, "sz": 17, "c": LIGHT, "space_after": 8} for it in items])
txt(s, Inches(0.7), Inches(5.75), Inches(12), Inches(1.0),
    [{"segs":[{"t":"The invariant:  ","sz":16,"b":True,"c":ACCENT},
      {"t":"only the primary path touches live recall; shared tiers are read on demand and the legacy engine is being phased out.","sz":16,"c":LIGHT}]}])
footer(s, 8)

# ============ 9 SIBLINE BROKER ============
s = s_new(); kicker(s, "Bus · Sibline", ACCENT); accent_bar(s)
title(s, "Sibline: the realtime cross-agent bus")
card(s, Inches(0.7), Inches(1.85), Inches(3.0), Inches(1.3), "OLLIE", "CherryRd", ACCENT, head_sz=20, body_sz=16)
card(s, Inches(9.63), Inches(1.85), Inches(3.0), Inches(1.3), "KUKLA", "m1", PURPLE, head_sz=20, body_sz=16)
box(s, Inches(4.55), Inches(1.7), Inches(4.2), Inches(1.6), fill=CARD); box(s, Inches(4.55), Inches(1.7), Inches(4.2), Pt(5), fill=ACCENT2)
txt(s, Inches(4.55), Inches(1.95), Inches(4.2), Inches(1.1),
    [{"t":"NATS / JetStream broker","sz":18,"b":True,"c":WHITE,"align":PP_ALIGN.CENTER},
     {"t":"durable, ack-after-process","sz":16,"c":LIGHT,"align":PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)
arrow(s, Inches(3.75), Inches(2.1), col=ACCENT2); arrow(s, Inches(8.8), Inches(2.1), col=ACCENT2)
txt(s, Inches(0.7), Inches(3.7), Inches(12), Inches(2.8),
    [{"t":"Envelope v1:  {id, from, to, ts, kind, body}","sz":16,"b":True,"c":ACCENT2,"font":"Consolas","space_after":10},
     {"t":"\u2022  sibline.<target>.inbox  \u2014  direct, durable, reliable path","sz":17,"c":LIGHT,"space_after":6},
     {"t":"\u2022  sibline.broadcast  \u2014  room chatter, durable consumer per agent","sz":17,"c":LIGHT,"space_after":6},
     {"t":"\u2022  sibline.<self>.outbox  \u2014  audit feed (observable, not load-bearing)","sz":17,"c":LIGHT,"space_after":6},
     {"t":"\u2022  sibline.presence.<agent>  \u2014  ephemeral, latest-only","sz":17,"c":LIGHT}])
footer(s, 9)

# ============ 10 SUBJECT TREE / CONTRACT ============
s = s_new(); kicker(s, "Bus · Sibline", ACCENT); accent_bar(s)
title(s, "The v1 subject contract (stable)")
streams = [
    ("sibline-ollie", "sibline.ollie.>", ACCENT),
    ("sibline-kukla", "sibline.kukla.>", PURPLE),
    ("sibline-broadcast", "sibline.broadcast", ACCENT2),
]
y = Inches(1.9)
for name, subj, col in streams:
    box(s, Inches(0.7), y, Inches(12.0), Inches(0.95), fill=CARD)
    box(s, Inches(0.7), y, Pt(5), Inches(0.95), fill=col)
    txt(s, Inches(1.0), y+Inches(0.2), Inches(4.5), Inches(0.6),
        [{"t": name, "sz": 19, "b": True, "c": WHITE, "font": "Consolas"}])
    txt(s, Inches(6.0), y+Inches(0.24), Inches(6.0), Inches(0.5),
        [{"t": subj, "sz": 17, "c": col, "font": "Consolas"}])
    y += Inches(1.1)
txt(s, Inches(0.7), Inches(5.5), Inches(12), Inches(1.3),
    [{"segs":[{"t":"File storage, 7-day retention, 10k msgs. ","sz":16,"c":LIGHT},
      {"t":"Per-user grant must include publish: $JS.>","sz":16,"b":True,"c":WARN,"font":"Consolas"},
      {"t":" \u2014 the load-bearing JetStream gotcha (without it, consumer/ack ops fail).","sz":16,"c":LIGHT}]}])
footer(s, 10)

# ============ 11 SIX CHANNELS ============
s = s_new(); kicker(s, "Bus", ACCENT); accent_bar(s)
title(s, "Six channels, ranked by latency")
chans = [
    ("Sibline", "realtime broker \u2014 PRIMARY", ACCENT2),
    ("kukla-mail", "file mailbox \u2014 durable fallback", ACCENT),
    ("Telegram bridge", "3-way, Rick-visible ops chatter", ACCENT),
    ("Slack mpim", "3-way shared room (no bot\u2194bot DM)", GREY),
    ("Webhooks", "HMAC-signed, ~50s (LLM in path)", WARN),
    ("Transcript mirror", "read-only shared situational awareness", GREY),
]
x = Inches(0.7); w = Inches(6.05); gap = Inches(0.2)
for i,(name,desc,col) in enumerate(chans):
    col_i = i % 2; row = i // 2
    lx = x + col_i*(w+gap); ty = Inches(1.85) + row*Inches(1.5)
    box(s, lx, ty, w, Inches(1.3), fill=CARD); box(s, lx, ty, Pt(5), Inches(1.3), fill=col)
    txt(s, lx+Inches(0.25), ty+Inches(0.18), w-Inches(0.5), Inches(0.5),
        [{"t": name, "sz": 19, "b": True, "c": WHITE}])
    txt(s, lx+Inches(0.25), ty+Inches(0.7), w-Inches(0.5), Inches(0.5),
        [{"t": desc, "sz": 16, "c": LIGHT}])
footer(s, 11)

# ============ 12 SYMMETRY RULE ============
s = s_new(); kicker(s, "Bus · invariant", ACCENT); accent_bar(s)
title(s, "The symmetry rule")
card(s, Inches(0.7), Inches(1.8), Inches(5.85), Inches(2.4), "BEFORE \u2014 asymmetric",
     "Ollie\u2192Kukla: broker (realtime)\nKukla\u2192Ollie: file only (lagged)\n= looks like a bug", WARN, body_sz=17)
card(s, Inches(6.85), Inches(1.8), Inches(5.78), Inches(2.4), "AFTER \u2014 symmetric",
     "Every send does BOTH legs:\ndurable file + broker publish\n= same latency both ways", ACCENT2, body_sz=17)
box(s, Inches(0.7), Inches(4.55), Inches(11.93), Inches(1.5), fill=CARD)
box(s, Inches(0.7), Inches(4.55), Inches(11.93), Pt(5), fill=ACCENT2)
txt(s, Inches(1.0), Inches(4.85), Inches(11.3), Inches(1.0),
    [{"segs":[{"t":"VALIDATED:  ","sz":18,"b":True,"c":ACCENT2},
      {"t":"live ping\u2192pong round-trip closed both directions \u00b7 dual-witness (CherryRd + m1) \u00b7 3 streams with correct durable-consumer filters.","sz":17,"c":LIGHT}]}])
footer(s, 12)

# ============ 13 HARNESS INTEGRATION ============
s = s_new(); kicker(s, "Integration", WARN); accent_bar(s, WARN)
title(s, "Plugging a harness into Falda")
stages = [
    ("Harness", "Hermes / OpenClaw", ACCENT),
    ("Tap", "T0 \u2192 /stream/add", ACCENT),
    ("Gateway", "Falda :8077", ACCENT2),
    ("Store", "SQLite + vec", WARN),
]
x = Inches(0.7); w = Inches(2.75); gap = Inches(0.45); t = Inches(1.95); h = Inches(1.7)
for i,(name,body,col) in enumerate(stages):
    lx = x+i*(w+gap)
    box(s, lx, t, w, h, fill=CARD); box(s, lx, t, w, Pt(5), fill=col)
    txt(s, lx+Inches(0.2), t+Inches(0.25), w-Inches(0.4), Inches(0.5),
        [{"t": name, "sz": 19, "b": True, "c": WHITE}])
    txt(s, lx+Inches(0.2), t+Inches(0.85), w-Inches(0.4), Inches(0.7),
        [{"t": body, "sz": 16, "c": LIGHT, "font": "Consolas"}])
    if i<3: arrow(s, lx+w+Inches(0.04), t+Inches(0.6))
card(s, Inches(0.7), Inches(4.0), Inches(5.85), Inches(2.0), "Two modes",
     "DUAL-RUN \u2014 tap captures + validates alongside TDAI during cutover\nPRIMARY \u2014 Falda is the memory provider (one config flip away)", ACCENT, body_sz=16)
card(s, Inches(6.85), Inches(4.0), Inches(5.78), Inches(2.0), "Replication-grade",
     "deploy/launchd/*.template (REPLACE_ME tokens) + deploy/nats/\nNumbered INSTALL order ends in a ping\u2192pong verify step", WARN, body_sz=16)
footer(s, 13)

# ============ 14 DEPLOY TREE ============
s = s_new(); kicker(s, "Integration · deploy", WARN); accent_bar(s, WARN)
title(s, "The deploy kit \u2014 stand it up from scratch")
box(s, Inches(0.7), Inches(1.85), Inches(7.4), Inches(4.3), fill=CARD)
box(s, Inches(0.7), Inches(1.85), Pt(5), Inches(4.3), fill=ACCENT)
txt(s, Inches(1.0), Inches(2.1), Inches(7.0), Inches(3.9),
    [{"t":"falda/","sz":17,"b":True,"c":WHITE,"font":"Consolas","space_after":4},
     {"t":"  docs/HARNESS_INTEGRATION.md","sz":16,"c":ACCENT2,"font":"Consolas","space_after":4},
     {"t":"  KUKLA_DELTA.md","sz":16,"c":LIGHT,"font":"Consolas","space_after":4},
     {"t":"  deploy/nats/","sz":16,"c":WHITE,"font":"Consolas","space_after":4},
     {"t":"    nats-server.conf.template","sz":16,"c":LIGHT,"font":"Consolas","space_after":4},
     {"t":"    create-streams.sh","sz":16,"c":LIGHT,"font":"Consolas","space_after":4},
     {"t":"  deploy/launchd/","sz":16,"c":WHITE,"font":"Consolas","space_after":4},
     {"t":"    com.example.falda-gateway.template","sz":16,"c":LIGHT,"font":"Consolas","space_after":4},
     {"t":"    com.example.falda-tap-openclaw.template","sz":16,"c":LIGHT,"font":"Consolas","space_after":4},
     {"t":"    com.example.nats-subscriber.template","sz":16,"c":LIGHT,"font":"Consolas"}])
card(s, Inches(8.35), Inches(1.85), Inches(4.28), Inches(4.3), "All tokenized",
     "Every secret / path is a REPLACE_ME_* token.\n\nNo operator-specific values.\n\nA stranger replaces the tokens, runs the INSTALL order, and verifies with ping\u2192pong.", ACCENT2, body_sz=16)
footer(s, 14)

# ============ 15 VALIDATION STATUS ============
s = s_new(); kicker(s, "Status", ACCENT2); accent_bar(s, ACCENT2)
title(s, "What's green right now")
checks = [
    ("Falda gateway /healthz", "ok \u2014 tiers: stream / atoms / scenes / core / pools", ACCENT2),
    ("Origin-clean guard", "0 breaches repo-wide", ACCENT2),
    ("Sibline ping\u2192pong", "PASS both directions, dual-witness", ACCENT2),
    ("Broker streams", "3 present, correct durable-consumer filters", ACCENT2),
    ("Deploy templates", "tokenized, no secret leaks", ACCENT2),
    ("Harness doc", "replication-grade, on origin", ACCENT2),
]
y = Inches(1.8)
for label, detail, col in checks:
    box(s, Inches(0.7), y, Inches(12.0), Inches(0.72), fill=CARD)
    box(s, Inches(0.7), y, Pt(5), Inches(0.72), fill=col)
    txt(s, Inches(1.0), y+Inches(0.13), Inches(0.6), Inches(0.5), [{"t":"\u2713","sz":20,"b":True,"c":ACCENT2}])
    txt(s, Inches(1.6), y+Inches(0.15), Inches(4.6), Inches(0.45), [{"t": label, "sz": 17, "b": True, "c": WHITE}])
    txt(s, Inches(6.4), y+Inches(0.17), Inches(6.0), Inches(0.45), [{"t": detail, "sz": 16, "c": LIGHT}])
    y += Inches(0.82)
footer(s, 15)

# ============ 16 SUMMARY ============
s = s_new()
box(s, 0, 0, Inches(0.28), SH, fill=ACCENT2)
box(s, Inches(0.28), 0, Inches(0.06), SH, fill=ACCENT)
txt(s, Inches(0.9), Inches(0.7), Inches(11), Inches(0.8),
    [{"t": "SUMMARY", "sz": 16, "b": True, "c": ACCENT2, "font": "Consolas"}])
txt(s, Inches(0.9), Inches(1.6), Inches(11.7), Inches(5.0),
    [{"t":"\u2022  Falda \u2014 born-clean US-origin four-tier (T0\u2192T3) engine becoming the primary memory provider.","sz":20,"c":LIGHT,"space_after":14},
     {"t":"\u2022  TDAI \u2014 the legacy four-layer (L0\u2192L3) runtime being migrated from; same tier semantics, clean handoff.","sz":20,"c":LIGHT,"space_after":14},
     {"t":"\u2022  Two agents (Kukla/Hermes + Ollie/OpenClaw), one human, separate identities.","sz":20,"c":LIGHT,"space_after":14},
     {"t":"\u2022  Sibline \u2014 NATS/JetStream realtime bus; symmetric, dual-witness validated.","sz":20,"c":LIGHT,"space_after":14},
     {"t":"\u2022  UMP + vault \u2014 shared structured / cold memory, read on demand.","sz":20,"c":LIGHT,"space_after":14},
     {"t":"\u2022  Harness integration is replication-grade \u2014 stand up + verify from scratch.","sz":20,"c":LIGHT}])
footer(s, 16)

out = "/Users/stevens/.openclaw/workspace/tdai-memory-deliverables/tdai-memory-system.pptx"
prs.save(out); print("saved", out, "slides=", len(prs.slides))
