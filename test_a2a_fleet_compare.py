"""Tests for a2a-fleet-compare — deterministic, no network."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import a2a_fleet_compare as fc


def card(name="agent", pv="0.3", skills=None, caps=None, url=None, **kw):
    c = {"name": name, "description": "d", "protocolVersion": pv,
         "skills": skills or [], "capabilities": caps if caps is not None else {}}
    if url:
        c["url"] = url
    c.update(kw)
    return c


def skill(sid="s1", name="Do Thing"):
    return {"id": sid, "name": name, "description": "x", "tags": []}


class AuditTests(unittest.TestCase):
    def test_clean_fleet(self):
        f, s = fc.audit([("a.json", card(name="A", url="https://a", skills=[skill("s1", "Alpha")])),
                         ("b.json", card(name="B", url="https://b", skills=[skill("s2", "Beta")]))])
        self.assertEqual(f, [])
        self.assertEqual(s["skills"], 2)

    def test_duplicate_skill_id(self):
        f, s = fc.audit([("a.json", card(name="A", skills=[skill("s1", "Alpha")])),
                         ("b.json", card(name="B", skills=[skill("s1", "Beta")]))])
        self.assertEqual(s["dup_skill_ids"], 1)
        self.assertTrue(any("skill id 's1'" in m for _, m in f))
        self.assertEqual(f[0][0], "CRITICAL")

    def test_near_identical_skill_names(self):
        f, _ = fc.audit([("a.json", card(name="A", skills=[skill("s1", "Summarize Document")])),
                         ("b.json", card(name="B", skills=[skill("s2", "summarize document")]))])
        self.assertTrue(any("intent-based routing" in m for _, m in f))
        self.assertEqual([s for s, _ in f], ["WARNING"])

    def test_capability_conflict(self):
        f, s = fc.audit([("a.json", card(name="A", caps={"streaming": True})),
                         ("b.json", card(name="B", caps={"streaming": False}))])
        self.assertEqual(s["cap_conflicts"], 1)
        self.assertTrue(any("A2A#1377" in m for _, m in f))

    def test_version_heterogeneity(self):
        f, _ = fc.audit([("a.json", card(name="A", pv="0.3")),
                         ("b.json", card(name="B", pv="1.0"))])
        self.assertTrue(any("2 protocol versions" in m for _, m in f))

    def test_unknown_version_in_fleet(self):
        f, _ = fc.audit([("a.json", card(name="A", pv="0.3")),
                         ("b.json", card(name="B", pv="9.2.9"))])
        self.assertTrue(any("'9.2.9' is not a known" in m for _, m in f))

    def test_duplicate_agent_name(self):
        f, _ = fc.audit([("a.json", card(name="same-agent")),
                         ("b.json", card(name="Same Agent"))])
        self.assertTrue(any("declared by 2 cards" in m for _, m in f))

    def test_duplicate_url(self):
        f, _ = fc.audit([("a.json", card(name="A", url="https://x/y")),
                         ("b.json", card(name="B", url="https://x/y"))])
        self.assertTrue(any("one endpoint" in m for _, m in f))

    def test_non_object_card(self):
        f, _ = fc.audit([("a.json", card(name="A")), ("b.json", [1, 2])])
        self.assertTrue(any("not a JSON object" in m for _, m in f))

    def test_single_card_rejected(self):
        f, _ = fc.audit([("a.json", card(name="A"))])
        self.assertEqual(f[0][0], "CRITICAL")

    def test_no_skills_no_crash(self):
        f, s = fc.audit([("a.json", card(name="A")), ("b.json", card(name="B"))])
        self.assertEqual(f, [])


class CliTests(unittest.TestCase):
    DIR = os.path.dirname(os.path.abspath(__file__))

    def _write(self, obj, fname):
        p = os.path.join(self.DIR, fname)
        with open(p, "w") as f:
            json.dump(obj, f)
        return p

    def test_cli_clean_exit0(self):
        a = self._write(card(name="A"), "_tmp_fc_a.json")
        b = self._write(card(name="B"), "_tmp_fc_b.json")
        try:
            self.assertEqual(fc.main([a, b]), 0)
        finally:
            os.remove(a); os.remove(b)

    def test_cli_dirty_exit2(self):
        a = self._write(card(name="A", skills=[skill("dup", "X")]), "_tmp_fc_a.json")
        b = self._write(card(name="B", skills=[skill("dup", "Y")]), "_tmp_fc_b.json")
        try:
            self.assertEqual(fc.main([a, b]), 2)
        finally:
            os.remove(a); os.remove(b)

    def test_cli_one_card_usage_error(self):
        self.assertEqual(fc.main(["only.json"]), 2)

    def test_cli_missing_file(self):
        try:
            rc = fc.main(["/nope1.json", "/nope2.json"])
        except SystemExit as e:
            rc = e.code
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
