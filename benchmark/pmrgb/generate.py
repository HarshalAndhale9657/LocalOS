"""Deterministic synthetic generator for Personal-Memory-RGB v0.

Fabricated, self-consistent facts => unambiguous gold labels + freely releasable.
Everything is seeded for reproducibility. See ../../docs/05_BENCHMARK_Personal_Memory_RGB.md.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from .schema import Page, History, QAItem, Citation
from .chunk import chunk_text
from .simhash import simhash_hex

# --- fact universe ----------------------------------------------------------
DOMAINS = {
    "machine learning": ("model", [("parameter count", "billion parameters", (1, 70)),
                                    ("context window", "thousand tokens", (4, 200)),
                                    ("benchmark score", "points", (30, 95))]),
    "cycling": ("road bike", [("frame weight", "kilograms", (6, 11)),
                              ("gear count", "gears", (11, 24)),
                              ("wheel size", "inches", (26, 29))]),
    "home cooking": ("stand mixer", [("bowl capacity", "liters", (3, 7)),
                                     ("motor power", "watts", (300, 1200)),
                                     ("speed settings", "speeds", (3, 12))]),
    "astronomy": ("telescope", [("aperture", "millimeters", (60, 350)),
                                ("focal length", "millimeters", (400, 2000)),
                                ("magnification", "times", (20, 400))]),
    "index investing": ("index fund", [("expense ratio", "basis points", (2, 80)),
                                       ("holdings count", "holdings", (50, 3000)),
                                       ("dividend yield", "basis points", (50, 400))]),
}
ADJ = ["Nimbus", "Aster", "Vertex", "Lumen", "Cobalt", "Meridian", "Quartz", "Zephyr",
       "Falcon", "Onyx", "Cirrus", "Halcyon", "Pyxis", "Solace", "Tundra", "Vesper",
       "Marlin", "Cedar", "Obsidian", "Larkspur", "Basalt", "Cinder", "Drift", "Ember"]
NOUN = ["One", "Pro", "X", "Prime", "Neo", "Core", "Max", "Edge", "Nova", "Mark II",
        "Air", "Ultra", "Plus", "Studio", "Lite", "GT", "SE", "Turbo"]


class Entity:
    def __init__(self, eid, name, domain, noun, attrs, released, price, price_until):
        self.eid, self.name, self.domain, self.noun = eid, name, domain, noun
        self.attrs = attrs                # {label: (value:int, unit:str)}
        self.released = released          # int year
        self.price = price                # int USD (time-sensitive)
        self.price_until = price_until    # ISO date the price was last valid


def make_universe(rng: random.Random, n: int) -> list[Entity]:
    names = set()
    ents = []
    domains = list(DOMAINS)
    for i in range(n):
        while True:
            name = f"{rng.choice(ADJ)} {rng.choice(NOUN)}"
            if name not in names:
                names.add(name)
                break
        domain = domains[i % len(domains)]
        noun, specs = DOMAINS[domain]
        attrs = {label: (rng.randint(lo, hi), unit) for (label, unit, (lo, hi)) in specs}
        released = rng.randint(2016, 2025)
        price = rng.randint(1, 30) * 100 + rng.randint(0, 99)
        ents.append(Entity(f"e_{i:03d}", name, domain, noun, attrs, released, price, None))
    return ents


# --- page rendering ---------------------------------------------------------
def render_page(rng: random.Random, ent: Entity, read_at: datetime, pid: str):
    """Return (Page, fact_sentences dict). Price validity is set just before read_at
    so it is always 'stale' relative to the evaluation as_of."""
    ent.price_until = (read_at - timedelta(days=rng.randint(2, 6))).date().isoformat()
    sents = {}
    lines = [f"{ent.name} is a {ent.domain} {ent.noun}."]
    sents["_intro"] = lines[0]
    for label, (val, unit) in ent.attrs.items():
        s = f"The {label} of the {ent.name} is {val} {unit}."
        sents[label] = s
        lines.append(s)
    rel = f"The {ent.name} was released in {ent.released}."
    sents["released"] = rel
    lines.append(rel)
    pr = f"As of {ent.price_until}, the listed price of the {ent.name} was {ent.price} US dollars."
    sents["price"] = pr
    lines.append(pr)
    # a little boilerplate noise, as a real captured page would have
    lines.append("Home  ·  Reviews  ·  Specs  ·  Newsletter signup  ·  © Example Media.")
    text = "\n".join(lines)
    slug = ent.name.lower().replace(" ", "-")
    page = Page(page_id=pid, url=f"https://specs.example.com/{slug}",
                title=f"{ent.name} — specs & overview", read_at=read_at.isoformat() + "Z",
                text=text, chunks=chunk_text(text), simhash=simhash_hex(text))
    return page, sents


def _cite(page: Page, sentence: str) -> Citation:
    chunk = next((c for c in page.chunks if sentence in c.text), page.chunks[0])
    return Citation(page_id=page.page_id, chunk_id=chunk.chunk_id, url=page.url,
                    read_at=page.read_at, quote=sentence)


# --- history + items --------------------------------------------------------
def build_history(rng: random.Random, universe: list[Entity], idx: int, pages_per: int):
    hid = f"hist_{idx:03d}"
    chosen = rng.sample(universe, pages_per)
    base = datetime(2026, 7, 7, 9, 0, 0)
    meta = {}
    pages: list[Page] = []
    for j, ent in enumerate(chosen):
        read_at = base + timedelta(days=j * 2, hours=rng.randint(0, 8))
        pid = f"{hid}_p{j:02d}"
        page, sents = render_page(rng, ent, read_at, pid)
        pages.append(page)
        meta[pid] = {"ent": ent, "sents": sents, "read_at": read_at, "page": page}
    # inject one near-duplicate (revisit with a trivial edit) to exercise dedup
    if pages:
        src = pages[0]
        dup = Page(page_id=f"{hid}_pdup", url=src.url + "?ref=nav",
                   title=src.title, read_at=(base + timedelta(days=1)).isoformat() + "Z",
                   text=src.text + "\nShare this page.", chunks=chunk_text(src.text),
                   simhash=simhash_hex(src.text), near_dup_of=src.page_id)
        pages.append(dup)
    persona = "reads " + ", ".join(sorted({m["ent"].domain for m in meta.values()}))
    return History(hid, persona, pages), meta


def gen_items(rng: random.Random, hist: History, meta: dict, universe: list[Entity]):
    as_of = datetime(2026, 8, 1, 0, 0, 0).isoformat() + "Z"
    items: list[QAItem] = []
    pids = [p for p in meta]  # exclude the near-dup (not in meta)
    in_hist_ids = {meta[p]["ent"].eid for p in pids}
    n = 0

    def nid():
        nonlocal n
        n += 1
        return f"pmrgb_{hist.history_id}_{n:03d}"

    stable_attrs = lambda ent: [l for l in ent.attrs]  # all attrs are stable except price

    # --- answerable: single_hop (3) ---
    for pid in rng.sample(pids, min(3, len(pids))):
        m = meta[pid]; ent = m["ent"]; label = rng.choice(stable_attrs(ent))
        val, unit = ent.attrs[label]
        items.append(QAItem(nid(), hist.history_id,
            f"What is the {label} of the {ent.name}?", "single_hop", "answer",
            f"{val} {unit}", [_cite(m["page"], m["sents"][label])], as_of, "easy"))

    # --- answerable: multi_hop (2) — compare a shared attribute ---
    for _ in range(2):
        cand = [p for p in pids]
        if len(cand) < 2:
            break
        a, b = rng.sample(cand, 2)
        ea, eb = meta[a]["ent"], meta[b]["ent"]
        shared = set(ea.attrs) & set(eb.attrs)
        if not shared:
            continue
        label = rng.choice(sorted(shared))
        va = ea.attrs[label][0]; vb = eb.attrs[label][0]
        if va == vb:
            continue
        winner = ea if va > vb else eb
        items.append(QAItem(nid(), hist.history_id,
            f"Which has the higher {label}, the {ea.name} or the {eb.name}?",
            "multi_hop", "answer", winner.name,
            [_cite(meta[a]["page"], meta[a]["sents"][label]),
             _cite(meta[b]["page"], meta[b]["sents"][label])], as_of, "medium"))

    # --- answerable: time_scoped (2) ---
    for pid in rng.sample(pids, min(2, len(pids))):
        m = meta[pid]; ent = m["ent"]; day = m["read_at"].date().isoformat()
        items.append(QAItem(nid(), hist.history_id,
            f"Which {ent.domain} {ent.noun} did you read about on {day}?",
            "time_scoped", "answer", ent.name,
            [_cite(m["page"], m["sents"]["_intro"])], as_of, "medium"))

    # --- must-abstain: not_in_history (3) ---
    outside = [e for e in universe if e.eid not in in_hist_ids]
    for ent in rng.sample(outside, min(3, len(outside))):
        label = rng.choice(list(ent.attrs))
        items.append(QAItem(nid(), hist.history_id,
            f"What is the {label} of the {ent.name}?", "not_in_history", "abstain",
            None, [], as_of, "medium", abstain_reason="not_in_history"))

    # --- must-abstain: stale (2) — time-sensitive price now outdated ---
    for pid in rng.sample(pids, min(2, len(pids))):
        m = meta[pid]; ent = m["ent"]
        items.append(QAItem(nid(), hist.history_id,
            f"What is the current listed price of the {ent.name}?", "stale", "abstain",
            None, [], as_of, "hard", abstain_reason="stale"))

    # --- must-abstain: false_premise (2) — attribute from the wrong domain ---
    for pid in rng.sample(pids, min(2, len(pids))):
        m = meta[pid]; ent = m["ent"]
        foreign = [l for d, (_, specs) in DOMAINS.items() if d != ent.domain
                   for (l, _, _) in specs]
        foreign = [l for l in foreign if l not in ent.attrs]
        wrong = rng.choice(foreign) if foreign else "top speed"
        items.append(QAItem(nid(), hist.history_id,
            f"What is the {wrong} of the {ent.name}?", "false_premise", "abstain",
            None, [], as_of, "hard", abstain_reason="false_premise"))

    return items


def generate(seed: int, n_histories: int, pages_per: int, universe_size: int):
    rng = random.Random(seed)
    universe = make_universe(rng, universe_size)
    histories, items = [], []
    for i in range(n_histories):
        h, meta = build_history(rng, universe, i, pages_per)
        histories.append(h)
        items.extend(gen_items(rng, h, meta, universe))
    return histories, items
