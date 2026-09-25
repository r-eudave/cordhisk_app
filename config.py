import os
import shutil
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


def _user_data_dir():
	if sys.platform == "darwin":
		return os.path.join(os.path.expanduser("~/Library/Application Support"), "CORDHISK", "memory_files")
	return os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "CORDHISK", "memory_files")


def _copy_missing_data(source_dir, destination_dir):
	os.makedirs(destination_dir, exist_ok=True)
	for file_name in os.listdir(source_dir) if os.path.isdir(source_dir) else []:
		source_path = os.path.join(source_dir, file_name)
		destination_path = os.path.join(destination_dir, file_name)
		if os.path.isfile(source_path) and not os.path.exists(destination_path):
			try:
				shutil.copy2(source_path, destination_path)
			except OSError:
				pass


def _portable_data_dirs():
	directories = [os.path.join(APP_ROOT, "memory_files")]
	if getattr(sys, "frozen", False) and sys.platform == "darwin":
		executable_dir = os.path.dirname(os.path.abspath(sys.executable))
		directories.append(os.path.join(executable_dir, "memory_files"))
	return list(dict.fromkeys(directories))


_portable_data_dirs = _portable_data_dirs()
_portable_data_dir = next(
	(directory for directory in _portable_data_dirs if os.path.exists(os.path.join(directory, "000_cordhisk.db"))),
	next((directory for directory in _portable_data_dirs if os.path.isdir(directory)), _portable_data_dirs[0]),
)

if getattr(sys, "frozen", False) and sys.platform == "win32":
	APP_DATA_DIR = _user_data_dir()
	_copy_missing_data(_portable_data_dir, APP_DATA_DIR)
elif _writable_data_dir(_portable_data_dir):
	APP_DATA_DIR = _portable_data_dir
else:
	APP_DATA_DIR = _user_data_dir()
	_copy_missing_data(_portable_data_dir, APP_DATA_DIR)