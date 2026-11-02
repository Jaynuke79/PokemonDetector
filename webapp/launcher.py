"""
Desktop launcher for the web application.

Serves the Flask app on the loopback interface and opens it in the default
browser. This is what the Windows installer's Start Menu shortcut runs.
"""

import ctypes
import ctypes.wintypes
import os
import socket
import sys
import traceback
import webbrowser

HOST = "127.0.0.1"
PREFERRED_PORT = 5000
NO_BROWSER_ENV_VAR = "POKE_NO_BROWSER"
# windows/installer.iss names this in AppMutex.
RUNNING_MUTEX_NAME = "PokemonDetectorWebLauncher"


def hold_running_mutex():
    """Hold a named mutex until the process exits, on Windows.

    Setup and the uninstaller refuse to run while the mutex exists, because
    replacing or deleting the bundle under a running launcher would break it.
    """
    if sys.platform != "win32":
        return
    create_mutex = ctypes.WinDLL("kernel32").CreateMutexW
    create_mutex.argtypes = [
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.BOOL,
        ctypes.wintypes.LPCWSTR,
    ]
    create_mutex.restype = ctypes.wintypes.HANDLE
    if not create_mutex(None, False, RUNNING_MUTEX_NAME):
        print("Warning: installers will not be able to tell this app is running.")


# Werkzeug binds with SO_REUSEADDR, which on Windows lets two processes that
# both set it share a port, so the launcher binds its own socket without it.
def _listen_on(port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((HOST, port))
        listener.listen()
    except OSError:
        listener.close()
        raise
    return listener


def open_listener(preferred_port):
    """Listen on the loopback interface, on any free port if the preferred one fails.

    Any bind error counts as a failure because Windows reports ports it has
    reserved, as Hyper-V and WSL do, with a permission error, not "in use".

    Returns:
        A listening socket bound to 127.0.0.1
    """
    try:
        return _listen_on(preferred_port)
    except OSError:
        print(f"Port {preferred_port} is not available, using another port.")
        return _listen_on(0)


def open_browser(url):
    """Open url in the default browser unless NO_BROWSER_ENV_VAR is set."""
    if os.environ.get(NO_BROWSER_ENV_VAR):
        return
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error:
        opened = False
    if not opened:
        print(f"Could not open a browser. Please go to {url}", flush=True)


def serve(app, listener):
    """Serve app on listener until interrupted, opening the browser once it listens."""
    from werkzeug.serving import make_server

    server = make_server(HOST, 0, app, threaded=True, fd=listener.fileno())
    url = f"http://{HOST}:{server.port}"
    print(f"Pokemon Detector is running at {url}", flush=True)
    print("Close this window to stop it.", flush=True)
    open_browser(url)
    server.serve_forever()


def _pause_if_interactive():
    if sys.stdin is not None and sys.stdin.isatty():
        input("Press Enter to close this window.")


def run():
    """Load the model and serve the web app.

    Returns:
        Process exit code
    """
    hold_running_mutex()
    print("Starting Pokemon Detector, this can take a minute...", flush=True)
    # Importing webapp.app loads the model, so the message above has to come first.
    import webapp.app

    if webapp.app.model is None:
        print("Pokemon Detector cannot start without its model.", flush=True)
        print("Reinstalling may fix this.", flush=True)
        return 1

    with open_listener(PREFERRED_PORT) as listener:
        serve(webapp.app.app, listener)
    return 0


def main():
    try:
        exit_code = run()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        exit_code = 1
    if exit_code != 0:
        _pause_if_interactive()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
