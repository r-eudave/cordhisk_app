import os
import sys


def _application_root():
	if getattr(sys, "frozen", False):
		return os.path.dirname(os.path.abspath(sys.executable))
	return os.path.dirname(os.path.abspath(__file__))


APP_ROOT = _application_root()
APP_DATA_DIR = os.path.join(APP_ROOT, "memory_files")
os.makedirs(APP_DATA_DIR, exist_ok=True)