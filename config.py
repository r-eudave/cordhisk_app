import os
import shutil
import sqlite3
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


def _memory_count(path):
	try:
		with sqlite3.connect(path) as connection:
			return connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
	except (OSError, sqlite3.Error):
		return -1


def _database_has_memories(path):
	return _memory_count(path) > 0


def _copy_data_for_empty_database(source_dir, destination_dir):
	source_database = os.path.join(source_dir, "000_cordhisk.db")
	destination_database = os.path.join(destination_dir, "000_cordhisk.db")
	if (
		os.path.isfile(source_database)
		and _database_has_memories(source_database)
		and os.path.isfile(destination_database)
		and not _database_has_memories(destination_database)
	):
		os.makedirs(destination_dir, exist_ok=True)
		for file_name in os.listdir(source_dir):
			source_path = os.path.join(source_dir, file_name)
			destination_path = os.path.join(destination_dir, file_name)
			if os.path.isfile(source_path):
				try:
					shutil.copy2(source_path, destination_path)
				except OSError:
					pass


def _portable_data_dirs():
	directories = [os.path.join(APP_ROOT, "memory_files")]
	if getattr(sys, "frozen", False) and sys.platform == "darwin":
		executable_dir = os.path.dirname(os.path.abspath(sys.executable))
		contents_dir = os.path.dirname(executable_dir)
		directories.append(os.path.join(contents_dir, "Resources", "memory_files"))
		directories.append(os.path.join(executable_dir, "memory_files"))
	return list(dict.fromkeys(directories))


def _best_data_dir(directories):
	return max(
		directories,
		key=lambda directory: _memory_count(os.path.join(directory, "000_cordhisk.db")),
	)


_portable_data_dirs = _portable_data_dirs()
_user_data_dir_path = _user_data_dir()
_portable_data_dir = _best_data_dir(_portable_data_dirs)
_source_data_dir = _best_data_dir(_portable_data_dirs + [_user_data_dir_path])

if _writable_data_dir(_portable_data_dir):
	APP_DATA_DIR = _portable_data_dir
else:
	APP_DATA_DIR = _user_data_dir_path

if _source_data_dir != APP_DATA_DIR:
	_copy_missing_data(_source_data_dir, APP_DATA_DIR)
	_copy_data_for_empty_database(_source_data_dir, APP_DATA_DIR)