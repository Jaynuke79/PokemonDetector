import re
import socket
import sys
import threading
import urllib.request
from pathlib import Path

import pytest
from werkzeug.serving import make_server

from webapp import launcher

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def occupied_port():
    with socket.socket() as holder:
        holder.bind((launcher.HOST, 0))
        holder.listen()
        yield holder.getsockname()[1]


@pytest.fixture
def browser_calls(monkeypatch):
    calls = []
    monkeypatch.delenv(launcher.NO_BROWSER_ENV_VAR, raising=False)
    monkeypatch.setattr(
        launcher.webbrowser, "open", lambda url: calls.append(url) or True
    )
    return calls


def test_open_listener_binds_only_to_loopback():
    with launcher.open_listener(0) as listener:
        assert listener.getsockname()[0] == "127.0.0.1"


def test_open_listener_uses_the_preferred_port_when_free():
    with launcher.open_listener(0) as probe:
        free_port = probe.getsockname()[1]

    with launcher.open_listener(free_port) as listener:
        assert listener.getsockname()[1] == free_port


def test_open_listener_falls_back_when_the_preferred_port_is_taken(
    occupied_port, capsys
):
    with launcher.open_listener(occupied_port) as listener:
        port = listener.getsockname()[1]

    assert port not in (occupied_port, 0)
    assert f"Port {occupied_port} is not available" in capsys.readouterr().out


def test_open_browser_opens_the_url(browser_calls):
    launcher.open_browser("http://127.0.0.1:5000")

    assert browser_calls == ["http://127.0.0.1:5000"]


def test_open_browser_is_suppressed_by_the_env_var(browser_calls, monkeypatch):
    monkeypatch.setenv(launcher.NO_BROWSER_ENV_VAR, "1")

    launcher.open_browser("http://127.0.0.1:5000")

    assert browser_calls == []


@pytest.mark.parametrize(
    "failing_open",
    [
        lambda _url: False,
        lambda _url: (_ for _ in ()).throw(launcher.webbrowser.Error("no browser")),
    ],
)
def test_open_browser_prints_the_url_when_no_browser_opens(
    monkeypatch, capsys, failing_open
):
    monkeypatch.delenv(launcher.NO_BROWSER_ENV_VAR, raising=False)
    monkeypatch.setattr(launcher.webbrowser, "open", failing_open)

    launcher.open_browser("http://127.0.0.1:5000")

    assert "http://127.0.0.1:5000" in capsys.readouterr().out


def test_serve_answers_requests_by_the_time_the_browser_opens(
    webapp_module, stub_model, monkeypatch
):
    monkeypatch.setattr(webapp_module, "model", stub_model)
    statuses = []
    servers = []
    real_make_server = make_server

    def recording_make_server(*args, **kwargs):
        servers.append(real_make_server(*args, **kwargs))
        return servers[-1]

    def request_health_then_stop(url):
        # serve_forever has not started yet, so the request waits in the backlog
        # and shutdown has to come from a thread that outlives this call.
        def fetch():
            with urllib.request.urlopen(f"{url}/health", timeout=30) as response:
                statuses.append(response.status)
            servers[0].shutdown()

        threading.Thread(target=fetch, daemon=True).start()
        return True

    monkeypatch.setattr("werkzeug.serving.make_server", recording_make_server)
    monkeypatch.delenv(launcher.NO_BROWSER_ENV_VAR, raising=False)
    monkeypatch.setattr(launcher.webbrowser, "open", request_health_then_stop)

    with launcher.open_listener(0) as listener:
        launcher.serve(webapp_module.app, listener)

    assert statuses == [200]


def test_run_refuses_to_serve_without_a_model(webapp_module, monkeypatch, capsys):
    monkeypatch.setattr(webapp_module, "model", None)
    monkeypatch.setattr(
        launcher, "serve", lambda *_: pytest.fail("served without a model")
    )

    assert launcher.run() == 1
    assert "cannot start without its model" in capsys.readouterr().out


def test_run_serves_the_existing_flask_app(webapp_module, stub_model, monkeypatch):
    monkeypatch.setattr(webapp_module, "model", stub_model)
    served = []
    monkeypatch.setattr(launcher, "serve", lambda app, _listener: served.append(app))
    monkeypatch.setattr(launcher, "PREFERRED_PORT", 0)

    assert launcher.run() == 0
    assert served == [webapp_module.app]


def test_main_pauses_on_failure_when_interactive(monkeypatch):
    prompts = []
    monkeypatch.setattr(launcher, "run", lambda: 1)
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", prompts.append)

    assert launcher.main() == 1
    assert len(prompts) == 1


def test_main_reports_a_crash_and_pauses(monkeypatch, capsys):
    prompts = []

    def crash():
        raise RuntimeError("boom")

    monkeypatch.setattr(launcher, "run", crash)
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", prompts.append)

    assert launcher.main() == 1
    assert "boom" in capsys.readouterr().err
    assert len(prompts) == 1


def test_main_does_not_wait_for_input_when_not_interactive(monkeypatch):
    monkeypatch.setattr(launcher, "run", lambda: 1)
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: False, raising=False)
    monkeypatch.setattr(
        "builtins.input", lambda *_: pytest.fail("waited for input with no console")
    )

    assert launcher.main() == 1


def test_installer_waits_on_the_mutex_the_launcher_holds():
    installer = (REPO_ROOT / "windows" / "installer.iss").read_text()

    assert re.findall(r"^AppMutex=(.+)$", installer, re.MULTILINE) == [
        launcher.RUNNING_MUTEX_NAME
    ]


def test_hold_running_mutex_does_nothing_off_windows(monkeypatch):
    monkeypatch.setattr(launcher.sys, "platform", "linux")
    monkeypatch.setattr(
        launcher.ctypes,
        "WinDLL",
        lambda *_: pytest.fail("called a Windows API"),
        raising=False,
    )

    launcher.hold_running_mutex()


@pytest.mark.parametrize(("handle", "warns"), [(123, False), (None, True)])
def test_hold_running_mutex_creates_the_named_mutex(monkeypatch, capsys, handle, warns):
    calls = []

    class Kernel32:
        @staticmethod
        def CreateMutexW(*args):
            calls.append(args)
            return handle

    monkeypatch.setattr(launcher.sys, "platform", "win32")
    monkeypatch.setattr(
        launcher.ctypes, "WinDLL", lambda _name: Kernel32, raising=False
    )

    launcher.hold_running_mutex()

    assert calls == [(None, False, launcher.RUNNING_MUTEX_NAME)]
    assert ("Warning" in capsys.readouterr().out) is warns


def test_run_takes_the_mutex_before_loading_the_model(monkeypatch):
    monkeypatch.setattr(
        launcher,
        "hold_running_mutex",
        lambda: (_ for _ in ()).throw(RuntimeError("reached mutex")),
    )

    with pytest.raises(RuntimeError, match="reached mutex"):
        launcher.run()


def test_main_pauses_when_the_server_import_fails(
    webapp_module, stub_model, monkeypatch, capsys
):
    prompts = []
    monkeypatch.setattr(webapp_module, "model", stub_model)
    monkeypatch.setitem(sys.modules, "werkzeug.serving", None)
    monkeypatch.setattr(launcher, "PREFERRED_PORT", 0)
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", prompts.append)

    assert launcher.main() == 1
    assert "werkzeug.serving" in capsys.readouterr().err
    assert len(prompts) == 1
