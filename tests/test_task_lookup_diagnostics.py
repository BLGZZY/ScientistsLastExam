"""`find_task`'s failure message has to survive the tail-slice that reports it.

Every `frontier_eval/run_eval.py` reports a failed evaluation by keeping the last 500
characters of stderr, and `error_message` is one of the few keys a searcher can see. A
message that names the whole inventory is longer than that, so the reader gets a fragment of
the task list where the reason should be - the most common wrapper failure there is, since a
mistyped or unregistered task id is exactly what checkpoint 23 exists to catch.

These tests pin the properties that make the message usable rather than its wording.
"""
from __future__ import annotations

import unittest

from sle.registry import find_task, list_tasks

TAIL_SLICE = 500


class TaskLookupDiagnosticsTests(unittest.TestCase):
    def _message(self, name: str, include_uncertified: bool = True) -> str:
        with self.assertRaises(KeyError) as caught:
            find_task(name, include_uncertified=include_uncertified)
        # KeyError renders its argument repr'd; the payload is what callers format.
        return str(caught.exception.args[0])

    def test_message_fits_the_tail_slice_that_reports_it(self):
        for probe in ("NoSuchTaskAtAll", "Design", "Inference", "a"):
            with self.subTest(probe=probe):
                self.assertLess(len(self._message(probe)), TAIL_SLICE)

    def test_message_names_the_closest_match_by_public_id(self):
        message = self._message("LennardJones")
        self.assertIn("Chemistry/LennardJonesCluster", message)
        # The bare directory name is a legal argument to find_task, but the message reports
        # the stable public id so a reader is never handed a form they cannot look up.
        self.assertNotIn("lennardjonescluster", message)

    def test_count_comes_from_the_inventory_not_the_filtered_view(self):
        """On the default path `specs` holds only certified tasks.

        Reporting its length told the reader the repository has five tasks while they were
        asking about one of the other seventy-odd - a false statement about the inventory,
        produced while answering a question about a task that does exist.
        """
        inventory = len(list_tasks(None))
        certified = len(list_tasks())
        self.assertGreater(inventory, certified)  # otherwise this test proves nothing
        existing_but_uncertified = next(
            spec.task_id for spec in list_tasks(None)
            if spec.task_id not in {s.task_id for s in list_tasks()}
        )
        message = self._message(existing_but_uncertified, include_uncertified=False)
        self.assertIn("%d tasks are registered" % inventory, message)
        self.assertNotIn("%d tasks are registered" % certified, message)

    def test_certified_only_lookup_says_so(self):
        existing_but_uncertified = next(
            spec.task_id for spec in list_tasks(None)
            if spec.task_id not in {s.task_id for s in list_tasks()}
        )
        message = self._message(existing_but_uncertified, include_uncertified=False)
        self.assertIn("certified tasks only", message)
        self.assertIn("allow-uncertified", message)
        # The unfiltered path has nothing to disclaim.
        self.assertNotIn("certified tasks only", self._message("NoSuchTaskAtAll"))


if __name__ == "__main__":
    unittest.main()
