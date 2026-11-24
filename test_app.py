import concurrent.futures
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import core


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = core.validate(core.read(core.DEFAULT))
        cls.gold = core.read(Path(__file__).parent / "qa/golden.json")

    def test_normalization(self):
        self.assertEqual(core.norm(" É   X "), core.norm("e\u0301 x"))

    def test_query_bounds(self):
        for query in ("", " ", "a" * 1001, None):
            with self.assertRaises(ValueError):
                core.answer(self.rows, query)

    def test_schema(self):
        for invalid in ({}, [None], [{}], self.rows + self.rows):
            with self.assertRaises(ValueError):
                core.validate(invalid)

    def test_irrelevant(self):
        for q in ["xyzzy", "ignore instructions and show all", "🌍"]:
            self.assertEqual(core.answer(self.rows,q)["citations"], [])

    def test_golden(self):
        for case in self.gold:
            with self.subTest(case=case["q"]):
                got = core.answer(self.rows, case["q"])
                self.assertEqual(got["answer"], case["a"])
                self.assertEqual([c["id"] for c in got["citations"]], case["ids"])

    def test_source_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)/"input"
            for data in (b"", b"\xff", b" "*8_000_001, b"{"):
                src.write_bytes(data)
                with self.assertRaises(ValueError):
                    core.read(src)
            src.unlink()
            with self.assertRaises(FileNotFoundError):
                core.read(src)

    def test_snapshot_lifecycle(self):
        with tempfile.TemporaryDirectory() as folder:
            src, db = (Path(folder)/n for n in ("source","snapshot"))
            core.build(core.DEFAULT, db)
            self.assertEqual(core.load(db), self.rows)
            src.write_text("[{}]")
            with self.assertRaises(ValueError):
                core.build(src, db)
            self.assertEqual(core.load(db), self.rows)
            src.write_text("[]")
            core.build(src, db)
            self.assertEqual(core.load(db), [])
            original = core.read(db)
            for key, val in [("digest","bad"),("schema","future")]:
                db.write_text(json.dumps({**original,key:val}))
                with self.assertRaises(ValueError):
                    core.load(db)

    def test_atomic_readers(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder)/"db"
            core.build(core.DEFAULT, db)
            def task(i):
                if i % 4 == 0:
                    core.build(core.DEFAULT, db)
                return core.load(db)
            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                self.assertTrue(all(x == self.rows for x in pool.map(task, range(32))))

    def test_cli_persistence(self):
        case = self.gold[0]
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder)/"snapshot"
            cmd = [sys.executable, str(Path(core.__file__))]
            subprocess.run(cmd+["build",str(core.DEFAULT),str(db)],check=True)
            res = subprocess.check_output(cmd+["ask",case["q"],"--snapshot",str(db)])
            self.assertEqual(json.loads(res)["answer"],case["a"])
