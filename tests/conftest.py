import sqlite3

import pytest

from blog.db import migrate


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "blog.db")
    migrate(c)
    yield c
    c.close()
