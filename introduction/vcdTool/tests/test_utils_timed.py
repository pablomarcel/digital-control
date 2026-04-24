import time
from introduction.vcdTool.utils import timed

@timed
def add(a,b):
    # tiny sleep to ensure timing code executes
    time.sleep(0.001)
    return a+b

def test_timed_decorator():
    assert add(2,3) == 5
