"""See what your Part 1 pipelines produce on real data (course-provided).

    uv run python -m cs329z_hw1.show priority em-12167 [em-...]   # label one or more emails
    uv run python -m cs329z_hw1.show digest 2001-06-22 [--labels] [--limit N]  # the digest for one day
    uv run python -m cs329z_hw1.show bm25 "larchfield audit" [--k 5]    # search the archive with your index
    uv run python -m cs329z_hw1.show email_qa "Who leads the Basin Analytics move?"
    uv run python -m cs329z_hw1.show search_docs "parental leave" [--k 5]
    uv run python -m cs329z_hw1.show memory [DIR]   # a memory store (e.g. .lm_cache/chat_memory), or every persona's after an evaluation

Each command calls your adapters the way the tests do, on the grading model,
and prints the result with the cost and time of the calls. Repeating a
command with unchanged code is free, because the LM caches every reply.

``digest --labels`` also prints the label your run_priority gives each email
of the day, so you can see which pile each one landed in. Those calls are
the ones your digest already made, so they come from the cache. A day of
the archive holds about 280 emails (the live tests use about 30 per day);
``--limit N`` runs the digest on the first N emails of the day.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cs329z_hw1 import data  # noqa: E402
from cs329z_hw1.llm import LM  # noqa: E402

# ANSI colors, on when stdout is a terminal and NO_COLOR is not set.
_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
_CODES = {"bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33", "blue": "34", "cyan": "36"}


def paint(text, *styles: str) -> str:
    if not _COLOR or not styles:
        return str(text)
    return "".join(f"\033[{_CODES[s]}m" for s in styles) + str(text) + "\033[0m"


LABEL_STYLE = {"urgent": ("red", "bold"), "normal": ("green",), "ignore": ("dim",), "unknown": ("yellow", "bold")}


def label(category: str) -> str:
    return paint(category, *LABEL_STYLE.get(category, ("yellow",)))


def _email_header(email: dict) -> str:
    return (
        f"{paint(email['id'], 'cyan')}  {paint(email['date'][:16], 'dim')}  from {email.get('from', '')}\n"
        f"  {paint('subject:', 'dim')} {paint(email.get('subject') or '(no subject)', 'bold')}"
    )


def _finish(lm: LM, started: float) -> None:
    u = lm.usage()
    cached = f", {u['cached_calls']} from the cache" if u["cached_calls"] else ""
    print(paint(f"\n[{u['calls']} model calls{cached}; ${u['cost_usd']:.4f}; {time.time() - started:.1f} s]", "dim"))


def show_priority(args) -> None:
    from cs329z_hw1 import adapters

    by_id = {e["id"]: e for e in data.load_emails()}
    lm = LM(tag="show/priority")
    started = time.time()
    for email_id in args.ids:
        email = by_id.get(email_id)
        if email is None:
            print(f"{email_id}: no such email")
            continue
        result = adapters.run_priority(email, lm)
        print(_email_header(email))
        body = " ".join(email["body"].split())
        print(f"  {paint('body:', 'dim')} {body[:300]}{'...' if len(body) > 300 else ''}")
        print(f"  -> {label(result['category'])}: {result['reason']}\n")
    _finish(lm, started)


def show_digest(args) -> None:
    from cs329z_hw1 import adapters

    emails = data.emails_on(args.date)
    if not emails:
        sys.exit(f"No emails on {args.date}. The archive covers 2001-06-01 to 2001-08-31.")
    total = len(emails)
    if args.limit:
        emails = emails[: args.limit]
    print(paint(f"Running your digest on {len(emails)} of the {total} emails of {args.date}...", "dim"), flush=True)
    lm = LM(tag="show/digest")
    started = time.time()
    digest = adapters.run_daily_digest(emails, lm)
    print(paint(f"\nDigest for {args.date} ({len(emails)} emails, {len(digest.split())} words):\n", "bold"))
    print(digest)
    if args.labels:
        print(paint("\nLabels from your run_priority:", "bold"))
        for email in emails:
            result = adapters.run_priority(email, lm)
            print(f"  {label(result['category']):<{8 + (len(label(result['category'])) - len(result['category']))}} "
                  f"{paint(email['id'], 'cyan')}  {email.get('subject') or '(no subject)'}")
    _finish(lm, started)


_archive_index: dict = {}


def archive_index():
    """Your BM25 index over the archive, built once per process (a few seconds)."""
    if "index" not in _archive_index:
        from cs329z_hw1 import adapters

        archive = data.load_emails()
        started = time.time()
        index = adapters.run_bm25_build([data.email_text(e) for e in archive])
        print(paint(f"[index built over {len(archive)} emails in {time.time() - started:.1f} s]", "dim"), flush=True)
        _archive_index.update(archive=archive, index=index)
    return _archive_index["archive"], _archive_index["index"]


def show_bm25(args) -> None:
    from cs329z_hw1 import adapters

    archive, index = archive_index()
    started = time.time()
    hits = adapters.run_bm25_search(index, args.query, args.k)
    elapsed = (time.time() - started) * 1000
    print(paint(f"bm25({args.query!r}, k={args.k}) -> {len(hits)} results in {elapsed:.1f} ms\n", "bold"))
    for doc_id, score in hits:
        email = archive[doc_id]
        words = email["body"].split()
        body = " ".join(words[:100]) + (" ..." if len(words) > 100 else "")
        print(f"{paint(f'{score:8.3f}', 'yellow', 'bold')}  {_email_header(email)}\n  {body}\n")


def show_email_qa(args) -> None:
    from cs329z_hw1 import adapters

    archive, index = archive_index()
    lm = LM(tag="show/email_qa")
    started = time.time()
    returned: dict[str, dict] = {}
    hops = 0

    def search(query: str, k: int = 5) -> list[dict]:
        nonlocal hops
        hops += 1
        hits = [archive[doc_id] for doc_id, _ in adapters.run_bm25_search(index, query, k)]
        print(f"{paint(f'search {hops}:', 'bold')} {paint(query, 'yellow')}  {paint(f'(k={k}, {len(hits)} results)', 'dim')}")
        for e in hits[:5]:
            print(f"    {paint(e['id'], 'cyan')}  {e.get('subject') or '(no subject)'}")
        if len(hits) > 5:
            print(paint(f"    ... and {len(hits) - 5} more", "dim"))
        returned.update((e["id"], e) for e in hits)
        return hits

    print(f"{paint('Question:', 'bold')} {args.question}\n")
    result = adapters.run_email_qa(args.question, search, lm)
    print(f"\n{paint('Answer:', 'bold')} {result['answer'] if result['answer'] is not None else paint('(none found)', 'dim')}")
    print(paint("Support:", "bold"))
    for email_id in result["support"]:
        email = returned.get(email_id)
        print(f"  {_email_header(email) if email else email_id + '  (not returned by search)'}")
    _finish(lm, started)


def show_search_docs(args) -> None:
    from cs329z_hw1 import adapters

    index = adapters.run_build_doc_index(data.load_docs())
    results = adapters.run_search_docs(index, args.query, args.k)
    print(paint(f"search_docs({args.query!r}, {args.k}) -> {len(results)} results\n", "bold"))
    for r in results:
        print(f"{paint(r['doc_id'], 'cyan')}  {paint('(' + r['title'] + ')', 'dim')}\n  {r['snippet']}\n")


def _print_store(store: Path, label: str) -> None:
    files = sorted(f for f in store.rglob("*") if f.is_file())
    print(f"{paint(label, 'cyan')}  {paint('(empty)' if not files else '', 'dim')}")
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        try:
            text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except ValueError:
            pass
        print(paint(f"  {f.relative_to(store)}", "dim"))
        for line in text.splitlines():
            print(f"    {line}")
    print()


def show_memory(args) -> None:
    """A memory store (every file in the directory), or, for an evaluation
    run under runs/, every persona's store. With no argument: the latest
    evaluation run."""
    path = Path(args.path) if args.path else max(Path("runs").glob("sim-*"), default=None, key=lambda p: p.stat().st_mtime)
    if path is None or not path.is_dir():
        sys.exit(f"No such directory: {path or 'runs/sim-*'}. Give a memory directory (chat.py uses .lm_cache/chat_memory) or an evaluation run.")
    stores = sorted(path.glob("*.memory"))
    if stores:
        print(paint(f"Memory after {path}: {len(stores)} personas\n", "bold"))
        for store in stores:
            _print_store(store, store.name[:-len(".memory")])
    else:
        _print_store(path, str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one of your Part 1 pipelines and print what it produces.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("priority", help="label one or more emails by id")
    p.add_argument("ids", nargs="+")
    p.set_defaults(fn=show_priority)
    p = sub.add_parser("digest", help="the digest for one day, YYYY-MM-DD")
    p.add_argument("date")
    p.add_argument("--labels", action="store_true", help="also print each email's priority label")
    p.add_argument("--limit", type=int, default=None, metavar="N", help="use only the first N emails of the day")
    p.set_defaults(fn=show_digest)
    p = sub.add_parser("bm25", help="search the archive with your BM25 index")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p.set_defaults(fn=show_bm25)
    p = sub.add_parser("email_qa", help="answer a question over the archive")
    p.add_argument("question")
    p.set_defaults(fn=show_email_qa)
    p = sub.add_parser("memory", help="a memory store, or every persona's after an evaluation run")
    p.add_argument("path", nargs="?", default=None, help="a memory directory, or a runs/sim-* directory (default: the latest run)")
    p.set_defaults(fn=show_memory)
    p = sub.add_parser("search_docs", help="search the company documents")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p.set_defaults(fn=show_search_docs)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
