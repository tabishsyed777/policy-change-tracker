"""Measure production-line coverage and scaling on an expanded fixture corpus."""
import copy
import dis
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc
import types
import unittest

import core
import domain

ROOT=Path(__file__).parent.resolve()


def executable(code):
    lines={line for _,line in dis.findlinestarts(code) if line and line>0}
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            lines.update(executable(item))
    return lines


def main():
    files=[ROOT/name for name in ("core.py","common.py","domain.py","service.py","import_table.py","import_figure.py") if (ROOT/name).exists()]
    measured={str(path):set() for path in files}
    def trace(frame,event,arg):
        filename=frame.f_code.co_filename
        if filename not in measured: return None
        if event=="line": measured[filename].add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:
        suite=unittest.defaultTestLoader.discover(str(ROOT))
        result=unittest.TextTestRunner(verbosity=0).run(suite)
    finally:
        sys.settrace(None)
    if not result.wasSuccessful(): return 1
    coverage={}
    for p in files:
        lines=executable(compile(p.read_bytes(),str(p),"exec"))
        hit=measured[str(p)] & lines
        coverage[p.name]={"hit":len(hit),"executable":len(lines),"fraction":round(len(hit)/len(lines),3)}
    rows=core.validate(core.read(core.DEFAULT))
    cases=core.read(ROOT/"qa/golden.json")
    clones=[]
    # Add irrelevant but schema-valid namespaces while preserving all target cases.
    namespace_fields={
        "04":("metric",),"05":("figure",),"06":("en","hi","hinglish","question"),
        "07":("consumer","dependency"),"08":("topic",),"09":("incident",),
        "10":("title","keywords"),"11":("topic",),"12":("topic",)
    }[domain.NAME[:2]]
    for i in range(1,101):
        for row in rows:
            clone=copy.copy(row)
            for key in ("id",*namespace_fields):
                clone[key]=f"unrelated{i}-"+clone[key]
            clones.append(clone)
    start=time.perf_counter()
    tracemalloc.start()
    expanded=core.validate(rows+clones)
    timings=[]
    correct=0
    for case in cases:
        before=time.perf_counter()
        got=core.answer(expanded,case["q"])
        timings.append((time.perf_counter()-before)*1000)
        correct+=got["answer"]==case["a"] and [r["id"] for r in got["citations"]]==case["ids"]
    peak=tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    report={"coverage_in_process_main_thread":coverage,"scale_records":len(expanded),
            "scale_exact_answer_and_citations":correct/len(cases),"scale_p95_ms":sorted(timings)[int(.95*len(timings))],
            "peak_traced_bytes_during_validation_and_queries":peak,
            "scale_elapsed_seconds":time.perf_counter()-start,
            "tests_run":result.testsRun,"skips":len(result.skipped)}
    print(json.dumps(report,indent=2))
    return 0 if correct/len(cases)>=.95 and report["scale_p95_ms"]<=1500 else 1

if __name__=="__main__":
    raise SystemExit(main())
