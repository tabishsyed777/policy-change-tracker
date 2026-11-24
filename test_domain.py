import unittest
import core

class DomainTests(unittest.TestCase):
    def test_dates(self):
        rows=core.read(core.DEFAULT)
        for q in ("meal allowance on 2025-02-30","changes to meal allowance from 2025-09-01 to 2025-01-01"):
            self.assertIsNone(core.answer(rows,q)["answer"])

    def test_conflicting_revision(self):
        rows=core.read(core.DEFAULT)
        with self.assertRaises(ValueError): core.validate(rows+[{**rows[0],"id":"other"}])

    def test_challenge_queries(self):
        rows=core.validate(core.read(core.DEFAULT))
        for query,expected in core.read(core.DEFAULT.parent.parent/"qa/challenge.json"):
            with self.subTest(query=query):
                self.assertEqual(core.answer(rows,query)["answer"],expected)
