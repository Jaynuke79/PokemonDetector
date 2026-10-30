import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULT_PAGES = ["webapp/templates/index.html", "demo-vercel/public/index.html"]


@pytest.mark.parametrize("page", RESULT_PAGES)
def test_predictions_are_rendered_as_text(page):
    source = (REPO_ROOT / page).read_text()

    assert not re.search(r"insertAdjacentHTML|outerHTML|document\.write", source)
    assert re.findall(r"innerHTML\s*\+?=\s*([^;]*);", source) == ["''"]
    assert re.search(r"\.textContent\s*=\s*`[^`]*prediction\.class_name", source)
    assert re.search(r"\.textContent\s*=\s*`[^`]*prediction\.percentage", source)
