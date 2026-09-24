import os
import sys
import tempfile


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


def _writable_data_dir(directory):
	try:
		os.makedirs(directory, exist_ok=True)
		with tempfile.NamedTemporaryFile(dir=directory, prefix=".write-test-", delete=False) as handle:
			test_path = handle.name
		os.remove(test_path)
		return True
	except OSError:
		try:
			os.remove(test_path)
		except (NameError, OSError):
			pass
		return False


_portable_data_dir = os.path.join(APP_ROOT, "memory_files")
if _writable_data_dir(_portable_data_dir):
	APP_DATA_DIR = _portable_data_dir
else:
	_user_data_root = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
	APP_DATA_DIR = os.path.join(_user_data_root, "CORDHISK", "memory_files")
	os.makedirs(APP_DATA_DIR, exist_ok=True)