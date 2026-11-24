# Policy Change Tracker

Retrieve the rule effective on a calendar date or compare the policy in force at two endpoints, with revision-level evidence.

## Quick start

From this directory, run these commands with Python 3.12 or 3.13. The example corpus is fictional and runs offline with the standard library.

```sh
python3 core.py ask 'meal allowance on 2025-04-30'
python3 core.py build data/source.json snapshot.json
python3 core.py ask 'meal allowance on 2025-07-01' --snapshot snapshot.json
python3 -m unittest discover -v
python3 evaluate.py
```

## Asking questions

Use “meal allowance on 2025-04-30” or “Changes to meal allowance from 2025-02-01 to 2025-08-01”.

## Using your own sources

Use the records in `data/source.json` as a schema example. Supply unique citation IDs and usable source locators. Build a new snapshot after additions, edits, or deletions. A successful build atomically replaces the previous snapshot. Results contain the answer, retrieval method and source locators. Unsupported queries return `insufficient_evidence`.

Dates are inclusive and revisions stay effective until superseded. Comparison reports endpoint values and can skip intermediate changes.

See [QA.md](QA.md) for measured results, review status and release limits.
