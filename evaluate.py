"""Reproduce the frozen fixture evaluation and synchronized reader benchmark."""
import concurrent.futures
import hashlib
import json
import math
from pathlib import Path
import statistics
import tempfile
import threading
import time
import core

ROOT = Path(__file__).parent


def run():
    cases = core.read(ROOT / "qa/golden.json")
    rows = core.validate(core.read(core.DEFAULT))
    exact, citation, recall, grounded, refused = [], [], [], [], []
    observations = []
    for c in cases:
        got = core.answer(rows, c["q"])
        ids = [x["id"] for x in got["citations"]]
        exact.append(got["answer"] == c["a"])
        citation.append(ids == c["ids"])
        if c["ids"]:
            recall.append(len(set(ids[:5]) & set(c["ids"])) / len(set(c["ids"])))
            grounded.append(exact[-1] and citation[-1])
        else:
            refused.append(got["status"] == "insufficient_evidence")
        observations.append({"question": c["q"], **got})
    with tempfile.TemporaryDirectory() as folder:
        db = Path(folder)/"index"
        core.build(core.DEFAULT, db)
        barrier = threading.Barrier(50)
        def work(i):
            c = cases[i % len(cases)]
            barrier.wait(timeout=30)
            start = time.perf_counter()
            response = core.answer(core.load(db), c["q"])
            return (time.perf_counter()-start)*1000, response["answer"] == c["a"]
        with concurrent.futures.ThreadPoolExecutor(50) as pool:
            times, correct = zip(*pool.map(work, range(50)))
    metrics = dict(cases=len(cases), answer_accuracy=statistics.mean(exact),
                   citation_exact=statistics.mean(citation), recall_at_5=statistics.mean(recall),
                   grounded_answer_exact=statistics.mean(grounded), refusal=statistics.mean(refused),
                   concurrent_accuracy=statistics.mean(correct), p50_ms=statistics.median(times),
                   p95_ms=sorted(times)[math.ceil(.95*len(times))-1], records=len(rows),
                   source_bytes=core.DEFAULT.stat().st_size, concurrent_readers=50,
                   golden_sha256=hashlib.sha256((ROOT/"qa/golden.json").read_bytes()).hexdigest())
    passed = (metrics["answer_accuracy"] >= .85 and metrics["citation_exact"] >= .95
              and metrics["recall_at_5"] >= .8 and metrics["grounded_answer_exact"] >= .95
              and metrics["refusal"] >= .95 and metrics["p95_ms"] <= 1500
              and metrics["concurrent_accuracy"] >= metrics["answer_accuracy"]-.05)
    print(json.dumps({"automated_gates_pass":passed,"metrics":metrics,"observations":observations},
                     ensure_ascii=False,indent=2))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(run())
