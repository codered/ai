"""P0 violation: unbounded loop without termination guarantee."""


def process_items(items):
    """Process items with no iteration cap."""
    while True:  # P0: NASA Rule 2 — bound all loops
        for item in items:
            handle(item)


def handle(item):
    if item > 0:
        return item * 2
    return None
