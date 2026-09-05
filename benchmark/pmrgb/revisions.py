"""Wikipedia revision-pair miner for Personal-Memory-RGB v1 (stdlib only).

Purpose (docs/07 §4.2): produce REAL stale-vs-fresh items. For an article we take two
revisions R_old < R_new. Sentences whose *numbers* changed between them become `stale`
candidates (the page was "read" with R_old's text; the evaluation `as_of` is after R_new).
Sentences whose numbers are identical in both revisions become `time_sensitive_fresh`
candidates. This removes the "fact type predicts the label" shortcut that made v0 unusable.

Data sources (all public; be polite — we send a descriptive User-Agent and sleep between
calls, and cache every response on disk so re-runs are free):
  - MediaWiki Action API   : revision ids/timestamps in a date window
  - Wikimedia REST API     : rendered HTML of a specific revision

Usage:
  python -m pmrgb.revisions --title "Mumbai" --since 2024-01-01 --until 2026-09-01
  python -m pmrgb.revisions --titles-file titles.txt --out data/revisions

Output: JSONL of candidate pairs; each row is a *candidate* that still needs the NLI/human
gate (revert vandalism, unit changes, etc. are not filtered here).
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from html.parser import HTMLParser

UA = "Groundwork-PersonalMemoryRGB/0.1 (research benchmark; shahjay147@gmail.com)"
API = "https://en.wikipedia.org/w/api.php"
REST_HTML = "https://en.wikipedia.org/api/rest_v1/page/html/{title}/{revid}"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache", "wiki")
SLEEP_S = 0.6

_NUM = re.compile(r"(?<![\w.])[+-]?\d[\d,]*(?:\.\d+)?(?![\w])")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")


# --- HTTP with disk cache -----------------------------------------------------
def _cached_get(url: str) -> bytes:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE_DIR, key)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    time.sleep(SLEEP_S)
    with open(path, "wb") as f:
        f.write(data)
    return data


def fetch_revisions(title: str, since: str, until: str, limit: int = 500) -> list[dict]:
    """Revisions (oldest → newest) of `title` in [since, until] as {revid, timestamp, size}."""
    out: list[dict] = []
    cont: dict = {}
    while True:
        params = {
            "action": "query", "prop": "revisions", "titles": title, "format": "json",
            "formatversion": "2", "rvprop": "ids|timestamp|size", "rvlimit": "50",
            "rvdir": "newer", "rvstart": f"{since}T00:00:00Z", "rvend": f"{until}T23:59:59Z",
            **cont,
        }
        data = json.loads(_cached_get(API + "?" + urllib.parse.urlencode(params)))
        pages = data.get("query", {}).get("pages", [])
        if not pages or "missing" in pages[0]:
            return []
        out.extend(pages[0].get("revisions", []))
        cont = data.get("continue", {})
        if not cont or len(out) >= limit:
            break
    return out[:limit]


# --- HTML → paragraph text ------------------------------------------------------
class _ParaExtractor(HTMLParser):
    """Keep only body <p> text; drop tables, refs, infoboxes, math, styles, scripts.

    Uses an explicit tag stack so a skipped subtree (e.g. <sup class="reference">[30]</sup>,
    which contains nested <a>/<span>) is dropped *entirely*; the earlier counter approach let
    reference numbers leak into sentences and be mis-detected as fact changes.
    """
    SKIP_TAGS = {"table", "style", "script", "sup", "math", "figure", "figcaption", "ol", "ul"}
    SKIP_CLASS_HINTS = ("reference", "infobox", "navbox", "hatnote", "mw-editsection",
                        "thumb", "reflist", "noprint", "sidebar")
    VOID = {"br", "img", "hr", "wbr", "input", "meta", "link", "source", "col", "area", "base"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras: list[str] = []
        self._buf: list[str] = []
        self._stack: list[tuple[str, bool]] = []  # (tag, is_skip_root)
        self._skip_depth = 0
        self._in_p = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        cls = " ".join(v or "" for k, v in attrs if k == "class")
        is_skip = tag in self.SKIP_TAGS or any(h in cls for h in self.SKIP_CLASS_HINTS)
        self._stack.append((tag, is_skip))
        if is_skip:
            self._skip_depth += 1
        elif tag == "p" and not self._skip_depth:
            self._in_p += 1

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        # pop to the matching open tag (tolerates unbalanced markup)
        while self._stack:
            t, is_skip = self._stack.pop()
            if is_skip:
                self._skip_depth = max(0, self._skip_depth - 1)
            elif t == "p" and self._in_p:
                self._in_p -= 1
                text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
                text = re.sub(r"\[\s*(?:\d+|[a-z]|note \d+|citation needed)\s*\]", "", text, flags=re.I)
                if len(text) > 40:
                    self.paras.append(text)
                self._buf = []
            if t == tag:
                break

    def handle_data(self, data):
        if self._in_p and not self._skip_depth:
            self._buf.append(data)


def fetch_revision_at(title: str, when: str) -> dict | None:
    """The last revision of `title` at or before ISO date `when` ({revid, timestamp, size}).

    Used by the v1 corpus builder: every article is snapshotted at one fixed "read" date and one
    fixed "now" date, so all histories share a coherent timeline (docs/07 §4.2).
    """
    params = {
        "action": "query", "prop": "revisions", "titles": title, "format": "json",
        "formatversion": "2", "rvprop": "ids|timestamp|size", "rvlimit": "1",
        "rvdir": "older", "rvstart": f"{when}T23:59:59Z",
    }
    data = json.loads(_cached_get(API + "?" + urllib.parse.urlencode(params)))
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0] or not pages[0].get("revisions"):
        return None
    return pages[0]["revisions"][0]


def fetch_plaintext(title: str, revid: int) -> list[str]:
    """Body paragraphs of a specific revision (rendered HTML → text)."""
    url = REST_HTML.format(title=urllib.parse.quote(title.replace(" ", "_"), safe=""), revid=revid)
    html = _cached_get(url).decode("utf-8", errors="replace")
    p = _ParaExtractor()
    p.feed(html)
    return p.paras


def sentences(paras: list[str]) -> list[str]:
    out = []
    for para in paras:
        for s in _SENT_SPLIT.split(para):
            s = s.strip()
            if 30 <= len(s) <= 400:
                out.append(s)
    return out


# --- fact-change detection ------------------------------------------------------
@dataclass
class FactPair:
    title: str
    old_revid: int
    old_ts: str
    new_revid: int
    new_ts: str
    kind: str                # "changed" | "unchanged"
    old_sentence: str
    new_sentence: str
    old_numbers: list[str]
    new_numbers: list[str]
    similarity: float
    dated: bool = False      # sentence carries an explicit time anchor ("As of May 2024", "In 2023")
    unit_only: bool = False  # only a parenthesised unit conversion changed (e.g. "(28,050 ft)" -> "(28,126 ft)") — not a real fact change


_DATED = re.compile(r"\b(as of|in|since|by|until|between)\s+(january|february|march|april|may|june|july|august|"
                    r"september|october|november|december|\d{4}|(early|mid|late)[- ]\d{4})\b", re.I)
_PAREN = re.compile(r"\([^()]*\)")


def is_dated(s: str) -> bool:
    return bool(_DATED.search(s))


_CURRENCY_ANCHOR = re.compile(r"\b(as of|as at|to date|currently|since)\b", re.I)


def is_currency_claim(s: str) -> bool:
    """True for sentences that assert a CURRENT state ("As of May 2024, 340 people have died"),
    as opposed to describing a past event ("In 1975, the polka-dot jersey was introduced").

    Only current-state sentences make meaningful `time_sensitive_fresh` controls: a historical
    event that never changes is not evidence that the assistant tracked freshness correctly.
    """
    return bool(_CURRENCY_ANCHOR.search(s)) and bool(_DATED.search(s))


def unit_conversion_only(old: str, new: str) -> bool:
    """True if old and new are identical once parenthesised spans are removed (unit re-rounding)."""
    return _PAREN.sub("", old).strip() == _PAREN.sub("", new).strip() and old != new


_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
_ANCHOR = re.compile(
    r"\b(?:as of|in|since|by|until|during|through)\s+(?:the\s+)?"
    r"(?:(january|february|march|april|may|june|july|august|september|october|november|december)\s+)?"
    r"(\d{4})\b", re.I)


def time_anchor(s: str):
    """The sentence's leading time reference as a sortable (year, month) tuple, or None.

    "As of November 2022, 310 people have died" -> (2022, 11);  "In 2023, ..." -> (2023, 0).
    """
    m = _ANCHOR.search(s)
    if not m:
        return None
    month = _MONTHS.get((m.group(1) or "").lower(), 0)
    return (int(m.group(2)), month, m.span())


def classify_change(old: str, new: str) -> str:
    """Distinguish genuine staleness from a source correction. Returns stale|correction|reject.

    The distinguishing signal is whether the sentence's OWN time anchor moves forward:
      stale       "In 2023, ... 19.9% share"      -> "In 2024, ... 17.6% share"   (world advanced)
      correction  "In February 2004, ... $100m"   -> "In February 2004, ... $176m" (article was wrong)
      reject      anchor moves backward, is absent, or only the anchor itself changed
    Only `stale` items get a must-abstain gold label; corrections are a different phenomenon and
    are kept out of the class rather than silently mislabeled (docs/07 §4.2).
    """
    a_old, a_new = time_anchor(old), time_anchor(new)
    if not a_old or not a_new:
        return "reject"
    if a_new[:2] < a_old[:2]:
        return "reject"
    # compare the numbers OUTSIDE the anchor span, so a bare year bump isn't mistaken for a fact change
    rest_old = (old[: a_old[2][0]] + old[a_old[2][1]:])
    rest_new = (new[: a_new[2][0]] + new[a_new[2][1]:])
    if not numbers_really_changed(_nums(rest_old), _nums(rest_new)):
        return "reject"
    return "stale" if a_new[:2] > a_old[:2] else "correction"


def numbers_really_changed(old_nums: list[str], new_nums: list[str]) -> bool:
    """False when the numbers were merely reordered/added/removed (e.g. '170 mph (270 km/h)' ->
    '270 km/h (170 mph)', or '55 lakh (5.5 million)' -> '5.5 million'); True when at least one
    number was replaced by a different value, which is what a genuine stale fact looks like."""
    o, n = set(old_nums), set(new_nums)
    return not (o <= n or n <= o)


def _nums(s: str) -> list[str]:
    return [n.replace(",", "") for n in _NUM.findall(s)]


def _skeleton(s: str) -> str:
    """Sentence with numbers masked — used to check the *only* change is numeric."""
    return re.sub(r"\s+", " ", _NUM.sub("<N>", s)).strip().lower()


def align_fact_pairs(old_sents: list[str], new_sents: list[str], min_sim: float = 0.80) -> list[tuple]:
    """For each old sentence with numbers, find its best counterpart in the new revision.

    Returns tuples (old, new, kind, similarity).
      kind='changed'       numbers differ, non-numeric skeleton IDENTICAL (highest-precision stale candidates)
      kind='changed_fuzzy' numbers differ, skeleton near-identical (rephrased; needs the NLI/human gate)
      kind='unchanged'     sentence identical in both revisions (fresh candidates)
    """
    new_by_skel: dict[str, list[str]] = {}
    for s in new_sents:
        if _nums(s):
            new_by_skel.setdefault(_skeleton(s), []).append(s)
    new_set = set(new_sents)
    results = []
    for o in old_sents:
        on = _nums(o)
        if not on:
            continue
        if o in new_set:
            results.append((o, o, "unchanged", 1.0))
            continue
        cands = new_by_skel.get(_skeleton(o), [])
        if cands:
            n = cands[0]
            if _nums(n) != on:
                results.append((o, n, "changed", 1.0))
            continue
        # fuzzy fallback: near-identical skeletons (a word or two edited along with the number)
        best, best_r = None, 0.0
        osk = _skeleton(o)
        for skel, lst in new_by_skel.items():
            r = difflib.SequenceMatcher(None, osk, skel).ratio()
            if r > best_r:
                best, best_r = lst[0], r
        if best is not None and best_r >= min_sim and _nums(best) != on:
            results.append((o, best, "changed_fuzzy", round(best_r, 3)))
    return results


def mine_title(title: str, since: str, until: str, min_gap_days: int = 90,
               max_pairs_per_kind: int = 20) -> list[FactPair]:
    revs = fetch_revisions(title, since, until)
    if len(revs) < 2:
        return []
    old, new = revs[0], revs[-1]
    gap_days = (_ts(new["timestamp"]) - _ts(old["timestamp"])) / 86400
    if gap_days < min_gap_days:
        return []
    old_s = sentences(fetch_plaintext(title, old["revid"]))
    new_s = sentences(fetch_plaintext(title, new["revid"]))
    pairs = align_fact_pairs(old_s, new_s)
    out: list[FactPair] = []
    counts = {"changed": 0, "changed_fuzzy": 0, "unchanged": 0}
    for o, n, kind, sim in pairs:
        if counts[kind] >= max_pairs_per_kind:
            continue
        counts[kind] += 1
        out.append(FactPair(title, old["revid"], old["timestamp"], new["revid"], new["timestamp"],
                            kind, o, n, _nums(o), _nums(n), sim,
                            dated=is_dated(o), unit_only=(kind != "unchanged" and unit_conversion_only(o, n))))
    return out


def _ts(iso: str) -> float:
    from datetime import datetime, timezone
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


# --- CLI ------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", action="append", default=[], help="article title (repeatable)")
    ap.add_argument("--titles-file", help="one title per line")
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--until", default="2026-09-01")
    ap.add_argument("--min-gap-days", type=int, default=90)
    ap.add_argument("--out", default=None, help="output dir for pairs.jsonl (default: print summary only)")
    args = ap.parse_args(argv)
    try:  # Windows consoles default to cp1252; article text is Unicode
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    titles = list(args.title)
    if args.titles_file:
        with open(args.titles_file, encoding="utf-8") as f:
            titles += [l.strip() for l in f if l.strip() and not l.startswith("#")]
    if not titles:
        ap.error("give --title or --titles-file")

    rows: list[FactPair] = []
    for t in titles:
        try:
            pairs = mine_title(t, args.since, args.until, args.min_gap_days)
        except Exception as e:  # keep mining other titles
            print(f"[warn] {t}: {e}", file=sys.stderr)
            continue
        ch = sum(p.kind == "changed" for p in pairs)
        cf = sum(p.kind == "changed_fuzzy" for p in pairs)
        un = sum(p.kind == "unchanged" for p in pairs)
        print(f"{t:<40} changed={ch:<3} changed_fuzzy={cf:<3} unchanged={un:<3}")
        shown = 0
        for p in pairs:
            if p.kind == "changed" and shown < 2:
                shown += 1
                print(f"    OLD ({p.old_ts[:10]}): {p.old_sentence[:120]}")
                print(f"    NEW ({p.new_ts[:10]}): {p.new_sentence[:120]}")
        rows.extend(pairs)

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "pairs.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for p in rows:
                f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
        print(f"\nwrote {len(rows)} candidate rows -> {path}")
    total_ch = sum(p.kind == "changed" for p in rows)
    total_cf = sum(p.kind == "changed_fuzzy" for p in rows)
    total_un = sum(p.kind == "unchanged" for p in rows)
    prime = [p for p in rows if p.kind != "unchanged" and p.dated and not p.unit_only
             and numbers_really_changed(p.old_numbers, p.new_numbers)]
    print(f"\nTOTAL over {len(titles)} titles: changed={total_ch} changed_fuzzy={total_cf} unchanged={total_un}")
    print(f"PRIME stale candidates (numbers changed, explicitly dated, not a unit re-rounding): {len(prime)}")
    for p in prime[:6]:
        print(f"  [{p.title}] {p.old_sentence[:100]}  ==>  {p.new_sentence[:100]}")


if __name__ == "__main__":
    main()
