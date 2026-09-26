import os
import socket
import sys
import threading
import webbrowser
import logging
import tempfile


def _get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def _configure_logging():
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        application_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), "CORDHISK")
    elif getattr(sys, "frozen", False):
        application_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        application_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(application_dir, "cordhisk.log")
    try:
        os.makedirs(application_dir, exist_ok=True)
        with open(log_path, "a", encoding="utf-8"):
            pass
    except OSError:
        application_data = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        application_dir = os.path.join(application_data, "CORDHISK")
        os.makedirs(application_dir, exist_ok=True)
        log_path = os.path.join(application_dir, "cordhisk.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return log_path


LOG_PATH = _configure_logging()

try:
    from cordhisk import app
except Exception:
    logging.getLogger(__name__).exception("CORDHISK failed during startup")
    raise


if __name__ == "__main__":
    host = os.environ.get("CORDHISK_HOST", "0.0.0.0")
    port = int(os.environ.get("CORDHISK_PORT", "5000"))
    # Always open the local browser tab against localhost, even when serving on 0.0.0.0.
    browser_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{browser_host}:{port}/"
    logging.getLogger(__name__).info("Starting CORDHISK at %s; log file: %s", url, LOG_PATH)
    if host in {"0.0.0.0", "::"}:
        lan_ip = _get_lan_ip()
        if lan_ip:
            message = f"Also reachable on your network at http://{lan_ip}:{port}/"
            print(message)
            logging.getLogger(__name__).info(message)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
