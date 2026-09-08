import os
import subprocess
import sys
import unittest

from helpers import REFS, ScratchRepo

sys.path.insert(0, REFS)
import run as runner  # noqa: E402

TASK = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate
import taskkit


def apply():
    with open({out!r}, "a", encoding="utf-8") as fh:
        fh.write("{name}\\n")


def verify():
    gate.structural("ran", lambda: taskkit.file_contains({out!r}, "{name}"))


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''

FAILING = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate


def apply():
    pass


def verify():
    gate.structural("never", lambda: False)


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''


class TestRunner(ScratchRepo):
    def _plan(self, specs):
        os.makedirs("tasks", exist_ok=True)
        out = os.path.join(self.dir, "order.log")
        for name, template in specs:
            body = template.format(refs=REFS, out=out, name=name)
            self.write(os.path.join("tasks", name + ".py"), body)
        return out

    def test_tasks_run_in_order(self):
        out = self._plan([("task_01_a", TASK), ("task_02_b", TASK), ("task_10_c", TASK)])
        code = runner.main([self.dir])
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read().split(), ["task_01_a", "task_02_b", "task_10_c"])

    def test_discover_sorts_numerically_not_lexically(self):
        self._plan([("task_02_b", TASK), ("task_10_c", TASK)])
        names = [os.path.basename(p) for p in runner.discover(self.dir)]
        self.assertEqual(names, ["task_02_b.py", "task_10_c.py"])

    def test_stops_at_first_red_gate(self):
        out = self._plan([("task_01_a", TASK), ("task_02_bad", FAILING), ("task_03_c", TASK)])
        code = runner.main([self.dir])
        self.assertEqual(code, 1)
        with open(out, encoding="utf-8") as fh:
            self.assertNotIn("task_03_c", fh.read())

    def test_report_json_is_captured(self):
        self._plan([("task_01_a", TASK)])
        code, report = runner.run_task(os.path.join(self.dir, "tasks", "task_01_a.py"))
        self.assertEqual(code, 0)
        self.assertEqual(report["backend"], "hashline")
        self.assertEqual(report["tiers"][-1]["tier"], "T0")


if __name__ == "__main__":
    unittest.main()
