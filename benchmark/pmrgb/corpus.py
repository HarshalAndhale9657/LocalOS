"""Article pool for Personal-Memory-RGB v1: real Wikipedia pages with labeled stale/fresh facts.

Every article is snapshotted at fixed dates so all histories share one coherent timeline
(docs/07 §4.2):

    READ_DATES (2024-02-01, 2025-03-01)  the revision a persona "read" -> the page text in history
    NOW_DATE   (2026-09-01)              reality at evaluation time    -> what is true `as_of`

Two read dates give both long-stale and short-stale facts and spread reading over two years; the
pool is keyed "title@read_date" so both snapshots of an article coexist.

Comparing the read revision with NOW labels each numeric sentence in the read text:

    fresh   an "as of"-style CURRENT-state claim that is unchanged at NOW_DATE
    stale   the sentence's OWN time anchor moved forward and its numbers changed
            ("As of November 2022, 310 people have died on Everest" -> "As of May 2024, 340")
            => a question about it must ABSTAIN or answer with a staleness caveat.
            Changes where the anchor stayed put are *source corrections*, not staleness
            (Wikipedia fixing an error about a past event), and are excluded — see
            revisions.classify_change.
            => a time-sensitive question about it must be ANSWERED  (the control class that
               kills the "fact type predicts the label" shortcut v0 suffered from)
    stable  sentence is unchanged and undated => ordinary single-hop / multi-hop material

The pool is cached to data/v1/pool.jsonl, so history assembly and QA generation run offline.

Usage:
  python -m pmrgb.corpus --personas sources/personas_v1.json --out data/v1     # build/extend pool
  python -m pmrgb.corpus --titles-file sources/titles_v1_seed.txt --out data/v1
  python -m pmrgb.corpus --out data/v1 --stats                                  # report only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict, field

from .revisions import (
    fetch_revision_at, fetch_plaintext, sentences, align_fact_pairs,
    is_dated, is_currency_claim, unit_conversion_only, classify_change, _nums,
)

# Two read snapshots spread the histories over a realistic timeline and give both long-stale and
# short-stale facts; the pool is keyed by "title@read_date" so both coexist.
READ_DATES = ["2024-02-01", "2025-03-01"]
READ_DATE = READ_DATES[0]
NOW_DATE = "2026-09-01"


@dataclass
class StaleFact:
    read_sentence: str
    now_sentence: str
    read_numbers: list[str]
    now_numbers: list[str]
    exact: bool  # True when only the numbers differ (highest-precision candidates)
    read_anchor: str = ""   # the sentence's own time reference, e.g. "2022-11"
    now_anchor: str = ""


@dataclass
class Article:
    title: str
    url: str
    read_date: str          # the snapshot date this page was "read" at
    read_revid: int
    read_ts: str
    now_revid: int
    now_ts: str
    paragraphs: list[str]                      # page text AS READ (read-revision)
    stale_facts: list[StaleFact] = field(default_factory=list)
    fresh_facts: list[str] = field(default_factory=list)   # dated, unchanged
    stable_facts: list[str] = field(default_factory=list)  # undated numeric, unchanged

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @property
    def key(self) -> str:
        return f"{self.title}@{self.read_date}"

    @staticmethod
    def from_dict(d: dict) -> "Article":
        d = dict(d)
        d["stale_facts"] = [StaleFact(**s) for s in d.get("stale_facts", [])]
        return Article(**d)


def build_article(title: str, read_date: str = READ_DATE, now_date: str = NOW_DATE,
                  max_paragraphs: int = 40) -> Article | None:
    """Fetch both revisions of `title` and label its facts. None if the article is unusable."""
    read_rev = fetch_revision_at(title, read_date)
    now_rev = fetch_revision_at(title, now_date)
    if not read_rev or not now_rev or read_rev["revid"] == now_rev["revid"]:
        return None

    read_paras = fetch_plaintext(title, read_rev["revid"])[:max_paragraphs]
    if len(read_paras) < 3:
        return None
    now_paras = fetch_plaintext(title, now_rev["revid"])

    read_sents = sentences(read_paras)
    now_sents = sentences(now_paras)
    pairs = align_fact_pairs(read_sents, now_sents)

    stale: list[StaleFact] = []
    fresh: list[str] = []
    stable: list[str] = []
    corrections = 0
    for old, new, kind, _sim in pairs:
        if kind == "unchanged":
            # only current-state claims ("as of ...") count as fresh controls; a historical event
            # that merely mentions a year is ordinary stable material
            (fresh if is_currency_claim(old) else stable).append(old)
            continue
        if unit_conversion_only(old, new):
            continue
        verdict = classify_change(old, new)
        if verdict == "correction":
            corrections += 1  # the article was fixed; the world did not change -> not staleness
            continue
        if verdict != "stale":
            continue
        from .revisions import time_anchor
        ao, an = time_anchor(old), time_anchor(new)
        stale.append(StaleFact(old, new, _nums(old), _nums(new), exact=(kind == "changed"),
                               read_anchor=f"{ao[0]}-{ao[1]:02d}" if ao else "",
                               now_anchor=f"{an[0]}-{an[1]:02d}" if an else ""))

    if not (stale or fresh or stable):
        return None
    slug = title.replace(" ", "_")
    return Article(
        title=title, url=f"https://en.wikipedia.org/wiki/{slug}", read_date=read_date,
        read_revid=read_rev["revid"], read_ts=read_rev["timestamp"],
        now_revid=now_rev["revid"], now_ts=now_rev["timestamp"],
        paragraphs=read_paras, stale_facts=stale, fresh_facts=fresh, stable_facts=stable,
    )


# --- pool persistence -----------------------------------------------------------------
def pool_path(out_dir: str) -> str:
    return os.path.join(out_dir, "pool.jsonl")


def load_pool(out_dir: str) -> dict[str, Article]:
    p = pool_path(out_dir)
    if not os.path.exists(p):
        return {}
    pool = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                a = Article.from_dict(json.loads(line))
                pool[a.key] = a
    return pool


def save_pool(out_dir: str, pool: dict[str, Article]) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(pool_path(out_dir), "w", encoding="utf-8") as f:
        for t in sorted(pool):
            f.write(json.dumps(pool[t].to_dict(), ensure_ascii=False) + "\n")


def titles_from_personas(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    seen, out = set(), []
    for p in spec["personas"]:
        for pool in p["pools"].values():
            for t in pool:
                if t not in seen:
                    seen.add(t)
                    out.append(t)
    return out


def build_pool(titles: list[str], out_dir: str, *, read_dates: list[str] | None = None,
               now_date: str = NOW_DATE, refresh: bool = False) -> dict[str, Article]:
    read_dates = read_dates or READ_DATES
    pool = {} if refresh else load_pool(out_dir)
    todo = [(t, d) for d in read_dates for t in titles if f"{t}@{d}" not in pool]
    print(f"pool: {len(pool)} cached, {len(todo)} to fetch")
    for i, (t, read_date) in enumerate(todo, 1):
        try:
            a = build_article(t, read_date, now_date)
        except Exception as e:
            print(f"  [{i}/{len(todo)}] {t}@{read_date} ERROR {e}", file=sys.stderr)
            continue
        if not a:
            print(f"  [{i}/{len(todo)}] {t}@{read_date:<20} skip (no usable revisions/text)")
            continue
        pool[a.key] = a
        print(f"  [{i}/{len(todo)}] {a.key:<56} paras={len(a.paragraphs):<3} "
              f"stale={len(a.stale_facts):<2} fresh={len(a.fresh_facts):<3} stable={len(a.stable_facts)}")
        if i % 10 == 0:
            save_pool(out_dir, pool)  # checkpoint: fetching is slow, don't lose it
    save_pool(out_dir, pool)
    return pool


def stats(pool: dict[str, Article]) -> dict:
    return {
        "snapshots": len(pool),
        "articles": len({a.title for a in pool.values()}),
        "with_stale": sum(1 for a in pool.values() if a.stale_facts),
        "stale_facts": sum(len(a.stale_facts) for a in pool.values()),
        "stale_exact": sum(sum(1 for s in a.stale_facts if s.exact) for a in pool.values()),
        "fresh_facts": sum(len(a.fresh_facts) for a in pool.values()),
        "stable_facts": sum(len(a.stable_facts) for a in pool.values()),
        "avg_paragraphs": round(sum(len(a.paragraphs) for a in pool.values()) / max(1, len(pool)), 1),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--personas", help="personas JSON whose pools list article titles")
    ap.add_argument("--titles-file", help="one title per line")
    ap.add_argument("--title", action="append", default=[])
    ap.add_argument("--out", default="data/v1")
    ap.add_argument("--read-date", action="append", default=[], help="repeatable; default two dates")
    ap.add_argument("--now-date", default=NOW_DATE)
    ap.add_argument("--refresh", action="store_true", help="ignore the cached pool and rebuild")
    ap.add_argument("--stats", action="store_true", help="report on the cached pool and exit")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if args.stats:
        print(json.dumps(stats(load_pool(args.out)), indent=2))
        return

    titles = list(args.title)
    if args.personas:
        titles += titles_from_personas(args.personas)
    if args.titles_file:
        with open(args.titles_file, encoding="utf-8") as f:
            titles += [l.strip() for l in f if l.strip() and not l.startswith("#")]
    if not titles:
        ap.error("give --personas, --titles-file or --title")
    seen, uniq = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    if args.limit:
        uniq = uniq[: args.limit]

    pool = build_pool(uniq, args.out, read_dates=args.read_date or READ_DATES,
                      now_date=args.now_date, refresh=args.refresh)
    print("\n" + json.dumps(stats(pool), indent=2))
    print(f"\npool -> {pool_path(args.out)}")


if __name__ == "__main__":
    main()
