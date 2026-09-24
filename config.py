import os
import sys


def _application_root():
	if getattr(sys, "frozen", False):
		executable_dir = os.path.dirname(os.path.abspath(sys.executable))
		contents_dir = os.path.dirname(executable_dir)
		bundle_dir = os.path.dirname(contents_dir)
		if (
			sys.platform == "darwin"
			and os.path.basename(executable_dir) == "MacOS"
			and os.path.basename(contents_dir) == "Contents"
			and bundle_dir.endswith(".app")
		):
			return os.path.dirname(bundle_dir)
		return executable_dir
	return os.path.dirname(os.path.abspath(__file__))


APP_ROOT = _application_root()
APP_DATA_DIR = os.path.join(APP_ROOT, "memory_files")
os.makedirs(APP_DATA_DIR, exist_ok=True)