import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rdbms.executor import Executor

@pytest.fixture(autouse=True)
def cleanup_tables():
    yield
    ex = Executor()
    try:
        ex.drop_all_tables()
    except Exception:
        pass
