"""
Desktop app for Pokemon detection.

A native Qt window that classifies images with the same model and detection
code as the CLI and web app. Run with --self-test IMAGE to classify one image
through the window and exit, which is how CI checks a built bundle.
"""

import argparse
import faulthandler
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from desktop.window import APP_NAME, MainWindow

SELF_TEST_TIMEOUT_MS = 10 * 60 * 1000
SCREENSHOT_SETTLE_MS = 250


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="poke-gui", description=f"{APP_NAME} desktop app."
    )
    parser.add_argument(
        "--self-test",
        metavar="IMAGE",
        help="Load the model, classify IMAGE through the window, print the "
        "predictions and exit with 0 on success, 1 on failure.",
    )
    parser.add_argument(
        "--screenshot",
        metavar="PNG",
        help="With --self-test, show the window and save a screenshot of it after "
        "classifying.",
    )
    args = parser.parse_args(argv)
    if args.screenshot and not args.self_test:
        parser.error("--screenshot needs --self-test")
    return args


def run_self_test(app, image_path, screenshot_path=None, models_dir=None):
    """Classify image_path through a MainWindow and print what its results show.

    Returns:
        0 if the image was classified (and the screenshot saved), else 1
    """
    window = MainWindow(models_dir=models_dir, show_dialogs=False)
    exit_codes = []

    def finish(code):
        if not exit_codes:
            exit_codes.append(code)
            app.exit(code)

    def save_screenshot():
        if window.grab().save(screenshot_path):
            print(f"Saved screenshot to {screenshot_path}")
            finish(0)
        else:
            print(f"Could not save a screenshot to {screenshot_path}", file=sys.stderr)
            finish(1)

    def on_results():
        for line in window.results.lines():
            print(line)
        if screenshot_path:
            QTimer.singleShot(SCREENSHOT_SETTLE_MS, save_screenshot)
        else:
            finish(0)

    def on_error(title, message):
        print(f"{title}: {message}", file=sys.stderr)
        finish(1)

    def on_timeout():
        print("Self-test timed out", file=sys.stderr)
        finish(1)

    def on_loaded():
        print(window.status_label.text())
        window.open_image(image_path)

    window.model_loaded.connect(on_loaded)
    window.results_shown.connect(on_results)
    window.error_reported.connect(on_error)
    timeout = QTimer(window, singleShot=True, interval=SELF_TEST_TIMEOUT_MS)
    timeout.timeout.connect(on_timeout)
    timeout.start()
    if screenshot_path:
        window.show()
    window.start()
    app.exec()
    window.close()
    window.shutdown()
    return exit_codes[0] if exit_codes else 1


def report_crashes_while_redirected():
    """Keep self-test output that a crash would otherwise lose in the buffer.

    A windowed exe has no stdout or stderr unless they are redirected.
    """
    if sys.stdout is not None:
        sys.stdout.reconfigure(line_buffering=True)
    if sys.stderr is not None and not faulthandler.is_enabled():
        faulthandler.enable(all_threads=True)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    if args.self_test:
        report_crashes_while_redirected()
        return run_self_test(app, args.self_test, args.screenshot)
    window = MainWindow()
    window.show()
    window.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
