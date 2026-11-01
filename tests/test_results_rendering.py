import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WEBAPP_PAGE = "webapp/templates/index.html"
DEMO_PAGE = "demo-vercel/public/index.html"
RESULT_PAGES = [WEBAPP_PAGE, DEMO_PAGE]
DRIFT_MESSAGE = (
    f"displayResults differs between {WEBAPP_PAGE} and {DEMO_PAGE}. "
    "The two copies are kept on purpose: apply the same edit to both pages."
)
DEMO_EMPTY_PREDICTIONS_GUARD = [
    "if (!predictions || predictions.length === 0) {",
    "errorDiv.textContent = 'No predictions returned. Please try again.';",
    "errorDiv.style.display = 'block';",
    "return;",
    "}",
]
GUARD_START = 2
GUARD_END = GUARD_START + len(DEMO_EMPTY_PREDICTIONS_GUARD)
GUARD_TEXT = "\n".join(DEMO_EMPTY_PREDICTIONS_GUARD)
AFTER_LIST_RESET = "predictionsList.innerHTML = '';\n"


def read_page(page):
    return (REPO_ROOT / page).read_text()


def display_results_lines(source):
    match = re.search(
        r"^( *)function displayResults\(predictions\) \{\n.*?^\1\}$",
        source,
        re.DOTALL | re.MULTILINE,
    )
    assert match, "displayResults not found"
    return [line.strip() for line in match.group(0).splitlines() if line.strip()]


def assert_rendering_matches(webapp_source, demo_source):
    demo_lines = display_results_lines(demo_source)
    assert demo_lines[GUARD_START:GUARD_END] == DEMO_EMPTY_PREDICTIONS_GUARD, (
        f"The empty-predictions guard in {DEMO_PAGE} changed. It is the one allowed "
        "difference between the pages and must stay as written."
    )
    del demo_lines[GUARD_START:GUARD_END]
    assert display_results_lines(webapp_source) == demo_lines, DRIFT_MESSAGE


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def change_guard_body(demo):
    return replace_once(
        demo,
        "errorDiv.textContent = 'No predictions returned. Please try again.';",
        "fetch('/collect', { credentials: 'include' });",
    )


def drop_guard_return(demo):
    return replace_once(
        demo,
        "return;\n            }\n\n            predictions",
        "}\n\n            predictions",
    )


def remove_guard(demo):
    return re.sub(
        r" *if \(!predictions \|\| predictions\.length === 0\) \{.*?\n *\}\n",
        "",
        demo,
        count=1,
        flags=re.DOTALL,
    )


def move_guard_below_rendering(demo):
    without_guard = remove_guard(demo)
    return replace_once(
        without_guard,
        "results.style.display = 'block';\n",
        f"{GUARD_TEXT}\nresults.style.display = 'block';\n",
    )


def edit_rendering(demo):
    return replace_once(demo, "`Confidence: ", "`Score: ")


@pytest.mark.parametrize("page", RESULT_PAGES)
def test_predictions_are_rendered_as_text(page):
    source = read_page(page)

    assert not re.search(r"insertAdjacentHTML|outerHTML|document\.write", source)
    assert re.findall(r"innerHTML\s*\+?=\s*([^;]*);", source) == ["''"]
    assert re.search(r"\.textContent\s*=\s*`[^`]*prediction\.class_name", source)
    assert re.search(r"\.textContent\s*=\s*`[^`]*prediction\.percentage", source)


def test_results_rendering_matches_between_pages():
    assert_rendering_matches(read_page(WEBAPP_PAGE), read_page(DEMO_PAGE))


@pytest.mark.parametrize(
    "edit_demo",
    [
        change_guard_body,
        drop_guard_return,
        remove_guard,
        move_guard_below_rendering,
        edit_rendering,
    ],
)
def test_drift_check_rejects_demo_edit(edit_demo):
    demo = read_page(DEMO_PAGE)
    edited = edit_demo(demo)
    assert edited != demo

    with pytest.raises(AssertionError):
        assert_rendering_matches(read_page(WEBAPP_PAGE), edited)


def test_drift_check_rejects_guard_added_to_webapp():
    webapp = replace_once(
        read_page(WEBAPP_PAGE), AFTER_LIST_RESET, f"{AFTER_LIST_RESET}{GUARD_TEXT}\n"
    )

    with pytest.raises(AssertionError, match="apply the same edit"):
        assert_rendering_matches(webapp, read_page(DEMO_PAGE))


def test_drift_check_ignores_indentation():
    demo = read_page(DEMO_PAGE)
    reindented = replace_once(
        demo, "results.style.display = 'block';", "    results.style.display = 'block';"
    )

    assert_rendering_matches(read_page(WEBAPP_PAGE), reindented)
