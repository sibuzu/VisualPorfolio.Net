from __future__ import annotations

import random
import string

PREFIX = "VP"


def new_project_id() -> str:
    return f"{PREFIX}-{_letters(6)}"


def _letters(n: int) -> str:
    return "".join(random.choice(string.ascii_uppercase) for _ in range(n))
