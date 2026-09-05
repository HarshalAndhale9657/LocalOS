"""Personal-Memory-RGB v1: history assembly + QA generation over the real-article pool.

Pipeline (docs/07 §4.2):

    pool.jsonl (pmrgb/corpus.py)            real Wikipedia pages, snapshotted at a read date,
                                            with facts labeled stale / fresh / stable
      -> assemble_histories()               personas read a coherent trajectory of pages, with
                                            realistic timestamps, boilerplate and near-duplicates
      -> generate_items()                   teacher writes questions grounded in specific
                                            sentences; every item passes an automatic gate
      -> split by history AND source article (no article leaks across train/dev/test)

Classes produced here: single_hop, multi_hop, time_sensitive_fresh, time_scoped, stale,
not_in_history, false_premise. (distractor_heavy and stored_injection are added by a later pass.)

Usage:
  python -m pmrgb.generate_v1 --pool data/v1 --out data/v1 --histories 40 --seed 7
  python -m pmrgb.generate_v1 --pool data/v1 --out data/v1 --histories 2 --dry-run   # inspect
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta

from .chunk import chunk_text
from .corpus import Article, load_pool, NOW_DATE
from .schema import Page, History, QAItem, Citation, Chunk
from .simhash import simhash_hex
from .teacher import Teacher

AS_OF = f"{NOW_DATE}T00:00:00Z"
BOILERPLATE = [
    "Main page  Contents  Current events  Random article  About Wikipedia  Contact us",
    "From Wikipedia, the free encyclopedia",
    "This article needs additional citations for verification.",
    "Categories: Articles with short description  Use dmy dates from July 2024",
]

# --- teacher prompts ---------------------------------------------------------------------
Q_SYSTEM = (
    "You write evaluation questions for a personal-memory QA benchmark. "
    "Given one SENTENCE from a web page the user read, write a single natural question whose "
    "complete answer is contained in that sentence, plus the short answer span. "
    "The question must NOT quote the sentence, must NOT reveal the answer, and must name the "
    "subject explicitly so it makes sense on its own (never 'this' or 'the company'). "
    "The answer must be a short span copied from the sentence (a number with its unit, a name, "
    "or a date). Reply with JSON only: {\"question\": \"...\", \"answer\": \"...\"}"
)
MULTI_SYSTEM = (
    "You write multi-hop questions for a personal-memory QA benchmark. Given TWO sentences from "
    "two different pages the user read, write one question that can only be answered by combining "
    "BOTH sentences (for example comparing two quantities), plus the short answer. Name both "
    "subjects explicitly. Reply with JSON only: {\"question\": \"...\", \"answer\": \"...\"}"
)
FALSE_PREMISE_SYSTEM = (
    "You write false-premise questions for a benchmark that tests whether an assistant corrects "
    "wrong assumptions instead of playing along. Given a SENTENCE the user read, write a question "
    "that presupposes something the sentence contradicts (for example a different quantity, an "
    "event that did not happen, or an attribute the subject does not have), while sounding "
    "natural and staying on the same subject. The question must be unanswerable as asked. "
    "Reply with JSON only: {\"question\": \"...\", \"false_premise\": \"...\"}"
)

_NUM = re.compile(r"\d[\d,.]*")


def _nums(s: str) -> set[str]:
    return {n.rstrip(".").replace(",", "") for n in _NUM.findall(s)}


def answer_supported(answer: str, sentence: str) -> bool:
    """Automatic gate: the answer must be lexically grounded in its source sentence.

    Numeric answers must reuse the sentence's numbers; textual answers must appear verbatim.
    This is a precision filter, not a substitute for the NLI + human gate (docs/07 §4.2).
    """
    a, s = answer.strip(), sentence
    if not a or len(a) > 120:
        return False
    an = _nums(a)
    if an:
        return an <= _nums(s)
    return a.lower() in s.lower()


def item_ok(question: str, answer: str, sentence: str) -> bool:
    """Full automatic gate for a generated answerable item."""
    if len(question.strip()) < 15 or "?" not in question:
        return False
    if not answer_supported(answer, sentence):
        return False
    # the answer must not already be sitting in the question (a weak teacher does this often:
    # "What did the jersey start awarding in 1975?" -> answer "1975")
    if answer.strip().lower() in question.lower():
        return False
    return True


# --- comparable quantities (for verifiable multi-hop) ---------------------------------------
_SCALE = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12,
          "lakh": 1e5, "crore": 1e7}
_UNITS = ("km", "kilometres", "kilometers", "miles", "mi", "metres", "meters", "m",
          "kg", "kilograms", "tonnes", "tons", "hours", "days", "years", "people",
          "%", "percent", "au", "employees", "stores", "passengers", "users", "speakers")
_QTY = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion|lakh|crore)?\s*"
    r"(km|kilometres|kilometers|miles|mi|metres|meters|m|kg|kilograms|tonnes|tons|hours|days|"
    r"years|people|%|percent|AU|employees|stores|passengers|users|speakers)\b", re.I)


def numeric_quantity(sentence: str):
    """First (value, canonical_unit) in the sentence, scaled by any million/billion modifier."""
    m = _QTY.search(sentence)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    val *= _SCALE.get((m.group(2) or "").lower(), 1.0)
    unit = m.group(3).lower()
    unit = {"kilometres": "km", "kilometers": "km", "mi": "miles", "metres": "m", "meters": "m",
            "kilograms": "kg", "tons": "tonnes", "percent": "%"}.get(unit, unit)
    return val, unit


# --- history assembly ---------------------------------------------------------------------
def _read_at(article: Article, rng: random.Random) -> datetime:
    """A timestamp at which the snapshot's text was demonstrably live: between the revision's
    own timestamp and the snapshot date."""
    lo = datetime.strptime(article.read_ts, "%Y-%m-%dT%H:%M:%SZ")
    hi = datetime.strptime(article.read_date, "%Y-%m-%d")
    if hi <= lo:
        hi = lo + timedelta(days=1)
    return lo + timedelta(seconds=rng.randint(0, int((hi - lo).total_seconds())))


def _page_from_article(a: Article, pid: str, read_at: datetime, rng: random.Random) -> Page:
    body = a.text
    noisy = f"{rng.choice(BOILERPLATE)}\n\n{body}\n\n{rng.choice(BOILERPLATE)}"
    chunks = [Chunk(c["chunk_id"], c["text"], tuple(c["offset"])) if isinstance(c, dict) else c
              for c in chunk_text(noisy)]
    return Page(page_id=pid, url=a.url, title=f"{a.title} - Wikipedia",
                read_at=read_at.isoformat() + "Z", text=noisy, chunks=chunks,
                simhash=simhash_hex(noisy))


def assemble_histories(pool: dict[str, Article], personas: list[dict], n_histories: int,
                       pages_per: int, rng: random.Random) -> tuple[list[History], list[dict]]:
    """Build histories and a parallel list of per-history metadata (which Article each page came
    from), which the item generator needs."""
    by_title: dict[str, list[Article]] = {}
    for a in pool.values():
        by_title.setdefault(a.title, []).append(a)

    histories, metas = [], []
    for i in range(n_histories):
        persona = personas[i % len(personas)]
        # keep each title's topic (the persona pool it came from) so multi-hop only compares
        # quantities from the same domain
        topic_of = {t: key for key, pl in persona["pools"].items() for t in pl if t in by_title}
        own = list(topic_of)
        other = [t for t in by_title if t not in topic_of]
        if len(own) < 3:
            continue
        rng.shuffle(own)
        n_own = min(len(own), max(3, int(pages_per * 0.8)))
        off = rng.sample(other, min(len(other), pages_per - n_own))
        titles = own[:n_own] + off

        hid = f"hist_{i:03d}"
        pages, pmeta = [], {}
        for j, t in enumerate(titles):
            a = rng.choice(by_title[t])           # which read-date snapshot this persona saw
            pid = f"{hid}_p{j:02d}"
            at = _read_at(a, rng)
            page = _page_from_article(a, pid, at, rng)
            pages.append(page)
            # off-topic pages get a unique topic so they never pair with anything
            pmeta[pid] = {"article": a, "page": page, "read_at": at,
                          "topic": topic_of.get(t, f"off_topic_{j}")}

        # one revisit near-duplicate, so dedup and distractor handling are exercised
        if pages:
            src = pages[0]
            dup_text = src.text + "\nShare this page."
            pages.append(Page(page_id=f"{hid}_pdup", url=src.url + "?utm_source=nav",
                              title=src.title, read_at=(datetime.strptime(src.read_at[:19], "%Y-%m-%dT%H:%M:%S")
                                                        + timedelta(days=3)).isoformat() + "Z",
                              text=dup_text, chunks=chunk_text(dup_text),
                              simhash=simhash_hex(dup_text), near_dup_of=src.page_id))

        pages.sort(key=lambda p: p.read_at)
        histories.append(History(hid, persona["description"], pages))
        metas.append({"history_id": hid, "persona": persona["id"], "pages": pmeta,
                      "titles": {m["article"].title for m in pmeta.values()}})
    return histories, metas


# --- item generation ------------------------------------------------------------------------
def _cite(page: Page, sentence: str) -> Citation | None:
    chunk = next((c for c in page.chunks if sentence[:60] in c.text), None)
    if not chunk:
        return None
    return Citation(page_id=page.page_id, chunk_id=chunk.chunk_id, url=page.url,
                    read_at=page.read_at, quote=sentence)


def generate_items(histories: list[History], metas: list[dict], pool: dict[str, Article],
                   teacher: Teacher, rng: random.Random, per_class: dict[str, int],
                   dry_run: bool = False) -> tuple[list[QAItem], dict]:
    items: list[QAItem] = []
    counts = {"kept": 0, "rejected_gate": 0, "rejected_parse": 0, "no_citation": 0}
    all_titles = {a.title for a in pool.values()}

    def ask(system: str, user: str, tag: str) -> dict | None:
        try:
            out = teacher.json(system, user, tag=tag)
            return out if isinstance(out, dict) else None
        except Exception as e:
            print(f"    teacher error: {str(e)[:120]}", file=sys.stderr)
            counts["rejected_parse"] += 1
            return None

    for hist, meta in zip(histories, metas):
        hid = hist.history_id
        n = 0

        def nid() -> str:
            nonlocal n
            n += 1
            return f"pmrgb1_{hid}_{n:03d}"

        pids = list(meta["pages"])
        prov_base = {"history": hid, "persona": meta["persona"], "teacher": teacher.model}

        def add(kind: str, question: str, decision: str, answer, cites, difficulty, extra=None,
                reason=None):
            items.append(QAItem(nid(), hid, question.strip(), kind, decision, answer, cites,
                                AS_OF, difficulty, abstain_reason=reason,
                                meta={**prov_base, **(extra or {})}))
            counts["kept"] += 1

        # --- single_hop: undated, unchanged numeric facts -------------------------------
        cand = [(p, s) for p in pids for s in meta["pages"][p]["article"].stable_facts]
        rng.shuffle(cand)
        made = 0
        for pid, sent in cand:
            if made >= per_class["single_hop"]:
                break
            m = meta["pages"][pid]
            out = ask(Q_SYSTEM, f"SUBJECT: {m['article'].title}\nSENTENCE: {sent}", "single_hop")
            if not out or not out.get("question") or not out.get("answer"):
                continue
            if not item_ok(str(out["question"]), str(out["answer"]), sent):
                counts["rejected_gate"] += 1
                continue
            c = _cite(m["page"], sent)
            if not c:
                counts["no_citation"] += 1
                continue
            add("single_hop", out["question"], "answer", str(out["answer"]), [c], "easy",
                {"source_sentence": sent, "source_title": m["article"].title})
            made += 1

        # --- time_sensitive_fresh: dated facts still true at as_of ----------------------
        cand = [(p, s) for p in pids for s in meta["pages"][p]["article"].fresh_facts]
        rng.shuffle(cand)
        made = 0
        for pid, sent in cand:
            if made >= per_class["time_sensitive_fresh"]:
                break
            m = meta["pages"][pid]
            out = ask(Q_SYSTEM, f"SUBJECT: {m['article'].title}\nSENTENCE: {sent}", "fresh")
            if not out or not out.get("question") or not out.get("answer"):
                continue
            if not item_ok(str(out["question"]), str(out["answer"]), sent):
                counts["rejected_gate"] += 1
                continue
            c = _cite(m["page"], sent)
            if not c:
                counts["no_citation"] += 1
                continue
            add("time_sensitive_fresh", out["question"], "answer", str(out["answer"]), [c], "medium",
                {"source_sentence": sent, "source_title": m["article"].title,
                 "still_true_at": NOW_DATE, "now_revid": m["article"].now_revid})
            made += 1

        # --- stale: the fact moved on between reading and as_of -------------------------
        cand = [(p, sf) for p in pids for sf in meta["pages"][p]["article"].stale_facts]
        rng.shuffle(cand)
        made = 0
        for pid, sf in cand:
            if made >= per_class["stale"]:
                break
            m = meta["pages"][pid]
            out = ask(Q_SYSTEM, f"SUBJECT: {m['article'].title}\nSENTENCE: {sf.read_sentence}", "stale")
            if not out or not out.get("question"):
                continue
            if not item_ok(str(out["question"]), str(out.get("answer", "")), sf.read_sentence):
                counts["rejected_gate"] += 1
                continue
            c = _cite(m["page"], sf.read_sentence)
            if not c:
                counts["no_citation"] += 1
                continue
            # gold: abstain OR answer with an explicit staleness caveat; the outdated value the
            # page supports is recorded so the evaluator can detect a confident stale answer.
            add("stale", out["question"], "abstain", None, [], "hard",
                {"source_sentence": sf.read_sentence, "now_sentence": sf.now_sentence,
                 "outdated_answer": str(out.get("answer", "")), "read_anchor": sf.read_anchor,
                 "now_anchor": sf.now_anchor, "source_title": m["article"].title,
                 "caveat_accepted": True},
                reason="stale")
            made += 1

        # --- multi_hop: compare one comparable quantity across two pages -------------------
        # Restricted to same-unit quantity comparisons so the gold answer is COMPUTED here and is
        # verifiable; the teacher only phrases the question. Free-form multi-hop from a small
        # teacher produced two unrelated questions stapled together (audit 2026-09-06).
        made = 0
        quantified = []
        for pid in pids:
            art = meta["pages"][pid]["article"]
            for sent in art.stable_facts + art.fresh_facts:
                q = numeric_quantity(sent)
                if q:
                    quantified.append((pid, sent, q[0], q[1]))
        rng.shuffle(quantified)
        for i, (pa, s1, v1, u1) in enumerate(quantified):
            if made >= per_class["multi_hop"]:
                break
            for pb, s2, v2, u2 in quantified[i + 1:]:
                if pa == pb or u1 != u2 or v1 == v2:
                    continue
                ma, mb = meta["pages"][pa], meta["pages"][pb]
                # same topic only: comparing "days a plant was closed" with "days in the yellow
                # jersey" is apples-to-oranges even when the units match (audit 2026-09-06)
                if ma["topic"] != mb["topic"] or ma["topic"].startswith("off_topic"):
                    continue
                ta, tb = ma["article"].title, mb["article"].title
                if ta == tb:
                    continue
                winner = ta if v1 > v2 else tb
                out = ask(MULTI_SYSTEM,
                          f"PAGE 1 ({ta}): {s1}\nPAGE 2 ({tb}): {s2}\n"
                          f"Both mention a quantity in {u1}. Ask which of the two is larger.",
                          "multi_hop")
                if not out or not out.get("question"):
                    break
                q = str(out["question"])
                if not (ta.lower() in q.lower() and tb.lower() in q.lower() and "?" in q):
                    counts["rejected_gate"] += 1
                    break
                c1, c2 = _cite(ma["page"], s1), _cite(mb["page"], s2)
                if not (c1 and c2):
                    counts["no_citation"] += 1
                    break
                add("multi_hop", q, "answer", winner, [c1, c2], "medium",
                    {"source_sentences": [s1, s2], "source_titles": [ta, tb],
                     "quantities": [[v1, u1], [v2, u2]], "answer_computed": True})
                made += 1
                break

        # --- time_scoped: what did I read, and when (deterministic) ----------------------
        # Only days on which exactly ONE page was read, else the question has several correct
        # answers (audit 2026-09-06).
        from collections import Counter as _Counter
        day_counts = _Counter(meta["pages"][p]["read_at"].date() for p in pids)
        unique_days = [p for p in pids if day_counts[meta["pages"][p]["read_at"].date()] == 1]
        rng.shuffle(unique_days)
        made = 0
        for pid in unique_days[: per_class["time_scoped"]]:
            m = meta["pages"][pid]
            day = m["read_at"].strftime("%d %B %Y")
            c = _cite(m["page"], m["article"].paragraphs[0][:60])
            if not c:
                counts["no_citation"] += 1
                continue
            add("time_scoped", f"Which page did I read on {day}?", "answer",
                m["article"].title, [c], "medium",
                {"read_at": m["read_at"].isoformat(), "source_title": m["article"].title})
            made += 1

        # --- not_in_history: real facts from articles this persona never read -------------
        outside = sorted(all_titles - meta["titles"])
        rng.shuffle(outside)
        made = 0
        for t in outside:
            if made >= per_class["not_in_history"]:
                break
            art = next(a for a in pool.values() if a.title == t)
            facts = art.stable_facts or art.fresh_facts
            if not facts:
                continue
            sent = rng.choice(facts)
            out = ask(Q_SYSTEM, f"SUBJECT: {art.title}\nSENTENCE: {sent}", "not_in_history")
            if not out or not out.get("question"):
                continue
            add("not_in_history", out["question"], "abstain", None, [], "medium",
                {"absent_title": art.title, "source_sentence": sent}, reason="not_in_history")
            made += 1

        # --- false_premise ----------------------------------------------------------------
        cand = [(p, s) for p in pids for s in (meta["pages"][p]["article"].stable_facts
                                               + meta["pages"][p]["article"].fresh_facts)]
        rng.shuffle(cand)
        made = 0
        for pid, sent in cand:
            if made >= per_class["false_premise"]:
                break
            m = meta["pages"][pid]
            out = ask(FALSE_PREMISE_SYSTEM, f"SUBJECT: {m['article'].title}\nSENTENCE: {sent}", "false_premise")
            if not out or not out.get("question"):
                continue
            add("false_premise", out["question"], "abstain", None, [], "hard",
                {"source_sentence": sent, "false_premise": out.get("false_premise", ""),
                 "source_title": m["article"].title}, reason="false_premise")
            made += 1

        print(f"  {hid}: {n} items  ({meta['persona']}, {len(hist.pages)} pages)")
        if dry_run:
            break
    return items, counts


# --- splitting -------------------------------------------------------------------------------
def assign_splits(items: list[QAItem], metas: list[dict], rng: random.Random,
                  ratios=(0.6, 0.2, 0.2)) -> dict:
    """Split by history AND by source article: an article's facts never appear in two splits."""
    hids = [m["history_id"] for m in metas]
    rng.shuffle(hids)
    n = len(hids)
    n_tr, n_dev = int(n * ratios[0]), int(n * ratios[1])
    split_of = {h: ("train" if i < n_tr else "dev" if i < n_tr + n_dev else "test")
                for i, h in enumerate(hids)}

    article_split: dict[str, str] = {}
    dropped = 0
    for it in items:
        s = split_of[it.history_id]
        titles = it.meta.get("source_titles") or [it.meta.get("source_title") or it.meta.get("absent_title")]
        titles = [t for t in titles if t]
        conflict = any(article_split.get(t, s) != s for t in titles)
        if conflict:
            it.split = None      # this article already belongs to another split -> drop the item
            dropped += 1
            continue
        for t in titles:
            article_split[t] = s
        it.split = s
    return {"by_history": split_of, "dropped_for_article_leak": dropped,
            "articles_assigned": len(article_split)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", default="data/v1")
    ap.add_argument("--out", default="data/v1")
    ap.add_argument("--personas", default="sources/personas_v1.json")
    ap.add_argument("--histories", type=int, default=40)
    ap.add_argument("--pages-per", type=int, default=14)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true", help="one history, print items, write nothing")
    for cls, dflt in [("single_hop", 3), ("multi_hop", 2), ("time_sensitive_fresh", 3),
                      ("time_scoped", 2), ("stale", 2), ("not_in_history", 3), ("false_premise", 2)]:
        ap.add_argument(f"--n-{cls.replace('_', '-')}", type=int, default=dflt)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    per_class = {c: getattr(args, f"n_{c}") for c in
                 ["single_hop", "multi_hop", "time_sensitive_fresh", "time_scoped",
                  "stale", "not_in_history", "false_premise"]}
    pool = load_pool(args.pool)
    if not pool:
        sys.exit(f"empty pool at {args.pool}; run: python -m pmrgb.corpus --personas {args.personas} --out {args.pool}")
    with open(args.personas, encoding="utf-8") as f:
        personas = json.load(f)["personas"]
    rng = random.Random(args.seed)
    teacher = Teacher()
    print(f"pool: {len(pool)} snapshots / {len({a.title for a in pool.values()})} articles; teacher={teacher.model}")

    histories, metas = assemble_histories(pool, personas, args.histories, args.pages_per, rng)
    print(f"assembled {len(histories)} histories")
    items, counts = generate_items(histories, metas, pool, teacher, rng, per_class, args.dry_run)

    if args.dry_run:
        for it in items[:14]:
            print(f"\n[{it.type}] gold={it.gold_decision}  {it.question}")
            print(f"    answer: {it.gold_answer}")
            if it.meta.get("source_sentence"):
                print(f"    source: {it.meta['source_sentence'][:110]}")
            if it.meta.get("now_sentence"):
                print(f"    now   : {it.meta['now_sentence'][:110]}")
        print(f"\ncounts: {counts}\nledger: {Teacher.ledger_summary()}")
        return

    info = assign_splits(items, metas, rng)
    kept = [it for it in items if it.split]
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "histories.jsonl"), "w", encoding="utf-8") as f:
        for h in histories:
            f.write(json.dumps(h.to_dict(), ensure_ascii=False) + "\n")
    with open(os.path.join(args.out, "items.jsonl"), "w", encoding="utf-8") as f:
        for it in kept:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"\ngate: {counts}")
    print(f"split: {info['articles_assigned']} articles assigned, {info['dropped_for_article_leak']} items dropped to prevent article leakage")
    print(f"kept {len(kept)} items across {len(histories)} histories")
    print("by type :", dict(Counter(it.type for it in kept)))
    print("by split:", dict(Counter(it.split for it in kept)))
    print("decision:", dict(Counter(it.gold_decision for it in kept)))
    print("ledger  :", Teacher.ledger_summary())
    print(f"-> {args.out}/histories.jsonl, {args.out}/items.jsonl")


if __name__ == "__main__":
    main()
