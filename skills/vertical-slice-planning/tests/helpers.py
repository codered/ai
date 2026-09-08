"""Shared scratch-repo fixture for taskkit tests."""
import os
import shutil
import sys
import tempfile
import unittest

REFS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
sys.path.insert(0, REFS)

SAMPLE = 'def send(req):\n    return _post(req)\n\n\ndef ping():\n    return "ok"\n'


class ScratchRepo(unittest.TestCase):
    """Gives each test a temp dir, a sample file, and a clean taskkit REPORT."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="taskkit-test-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self.cwd)
        self.write("client.py", SAMPLE)
        import taskkit
        taskkit.REPORT.update(backend="hashline", tiers=[], warnings=[])

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def read(self, name):
        with open(os.path.join(self.dir, name), encoding="utf-8") as fh:
            return fh.read()
