# Put pibus/ and the fake rgbmatrix package on sys.path so tests run without
# Raspberry Pi hardware or any installed deps beyond the standard library.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "stubs"))
sys.path.insert(0, os.path.dirname(HERE))
