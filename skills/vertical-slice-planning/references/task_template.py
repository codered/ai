"""Canonical task shapes. Copy one of these per task; delete the other block entirely, including its guard."""
import sys
import os

# Resolve taskkit in the plan root (one level above tasks/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import taskkit
from taskkit import Editor, ManualTask, gate

# ---------------------------------------------------------------- scripted --
KIND = "scripted"
TIER = "T2"
TOUCHES = ["client", "svc/orders"]
CROSSES = ["client -> orders HTTP"]


def apply():
    """Thread the retry setting from the client through to the orders service."""
    with Editor("client/http.py") as ed:
        ed.swap(
            ed.locate("    return self._send(req)"),
            ["    return self._send(req, retries=self.retries)"],
        )
    with Editor("svc/orders/handler.py") as ed:
        ed.insert_after(
            ed.locate("def handle(req):"),
            ["    retries = int(req.headers.get('x-retries', 0))"],
        )
    taskkit.create_file("svc/orders/retry.py", "MAX = 3\n")


def verify():
    gate.structural(
        "client passes retries",
        lambda: taskkit.file_contains("client/http.py", "retries=self.retries"),
    )
    gate.component("orders unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "svc/orders/tests"])
    gate.crossing("client reaches orders with a retry header", cmd=["./scripts/smoke_retry.sh"])


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))


# ------------------------------------------------------------------ manual --
# KIND = "manual"
#
# def apply():
#     raise ManualTask(
#         "Rewrite OrderService.dispatch() to take a RetryPolicy instead of an int.\n"
#         "Steps are in plan_superpowers.md, Task 07. The gate below is runnable now."
#     )
#
# def verify():
#     gate.structural("RetryPolicy in use", lambda: taskkit.file_contains("svc/orders/service.py", "RetryPolicy"))
#     gate.component("orders unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "svc/orders/tests"])
#
# if __name__ == "__main__":
#     raise SystemExit(gate.run(apply, verify))
