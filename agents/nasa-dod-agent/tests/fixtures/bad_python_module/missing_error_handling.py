"""P1 violation: catch-all bare except clause."""


def load_config(path):
    """Load config with unsafe exception handling."""
    try:
        with open(path) as f:
            return f.read()
    except:  # P1: bare except
        return None


def divide(a, b):
    return a / b  # No zero-check before division
