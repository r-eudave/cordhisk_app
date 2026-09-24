import os
import threading
import webbrowser

from cordhisk import app


if __name__ == "__main__":
    host = os.environ.get("CORDHISK_HOST", "127.0.0.1")
    port = int(os.environ.get("CORDHISK_PORT", "5000"))
    url = f"http://{host}:{port}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
