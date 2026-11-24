# Policy Change Tracker quality review

**Release status: pending human review.** The automated gates passed on the supplied fixtures. Real-corpus performance and independent human judgment remain unmeasured.

| Area | Check | Status | Evidence |
|---|---|---|---|
| A | Ingestion, duplicates, schema, malformed encoding, size cap | PASS | test_schema, test_source_errors, test_domain.py |
| A | Unicode normalization and length limits | PASS | test_normalization, test_query_bounds |
| A | Retrieval, synthesis, refusal, citation ordering | PASS | test_golden, test_irrelevant and domain tests |
| A | Learned embedding, learned reranking, prompt and remote generation | N/A | Offline deterministic retrieval and synthesis |
| A | Passage splitting and overlap | N/A | One structured evidence record per unit |
| B | Refresh, deletion, failed update, schema mismatch, checksum | PASS | test_snapshot_lifecycle |
| B | Concurrent reads and writes, restart, CLI | PASS | test_atomic_readers, test_cli_persistence |
| B | Cross-version execution | PASS | Python 3.12 and 3.13 unittest logs in qa/ |
| C | Golden answer accuracy ≥0.85 | PASS | 1.000 over 30 cases |
| C | Evidence Recall@5 ≥0.80 and exact citation list ≥0.95 | PASS | 1.000 and 1.000 |
| C | Grounded answer proxy ≥0.95 | PASS | 1.000 for answerable cases requiring both exact answer and citations |
| C | Refusal accuracy ≥0.95 | PASS | 1.000 on unsupported cases |
| D | 50 concurrent reads, p95 ≤1500 ms, accuracy drop ≤0.05 | PASS | p50 3.5 ms, p95 8.9 ms, concurrent accuracy 1.000 |
| D | Reproducibility and observability | PASS | evaluate.py emits metrics, outputs, golden fingerprint and route for answered questions |
| D | External model calls and billed tokens | N/A | No inference service or API dependency |
| D | Independent human spot-check of ≥10 outputs | PENDING | Review first ten outputs in qa/results.json against data/source.json and record verdicts |

**Scope and outstanding checks.** Dates are inclusive and revisions stay effective until superseded. Comparison reports endpoint values and can skip intermediate changes. The benchmark uses 12 synthetic source records and repeated in-process worker threads, each reopening the snapshot. It does not establish large-corpus throughput. Questions share fixture families. The grounded-answer proxy checks labeled evidence and is not an independent faithfulness assessment. No critical or high failures observed in the executed suite. Human review, real-source evaluation and whole-process RSS measurement remain open. Test files and per-case outputs are included.

## Additional checks

Four extra challenge queries exercise alternate phrasing or boundary conditions. See `qa/challenge.json` and `test_challenge_queries`. Expanding this corpus to 1212 records yielded 100.0% exact answers and citations on the original golden questions. The measured sequential p95 was 3.5 ms. The expanded set uses namespaced fixture records. It measures scale sensitivity, with limited topical diversity.

Run `python3 extra_checks.py` to regenerate scale results, Python allocation peak and per-file executable-line coverage. Coverage omits code executed in child processes and worker threads. The release baseline is in `qa/extended.json`.
