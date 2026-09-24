import os
import sys
import threading
import webbrowser
import logging


def _configure_logging():
    if getattr(sys, "frozen", False):
        application_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        application_dir = os.path.dirname(os.path.abspath(__file__))
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
    host = os.environ.get("CORDHISK_HOST", "127.0.0.1")
    port = int(os.environ.get("CORDHISK_PORT", "5000"))
    url = f"http://{host}:{port}/"
    logging.getLogger(__name__).info("Starting CORDHISK at %s; log file: %s", url, LOG_PATH)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
