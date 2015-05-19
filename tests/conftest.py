import os

import py
import pytest


@pytest.fixture()
def datadir():
    here = os.path.dirname(os.path.abspath(__file__))
    return py.path.local(os.path.join(here, 'raw'))
