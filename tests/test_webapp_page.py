import json
import re


def render_page(client):
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def read_predict_response_body(page):
    match = re.search(
        r"^( *)function readPredictResponse\(response\) \{\n(.*?)^\1\}$",
        page,
        re.DOTALL | re.MULTILINE,
    )
    assert match, "readPredictResponse not found"
    return match.group(2)


def test_predict_response_is_parsed_only_through_the_content_type_check(client):
    page = render_page(client)

    assert page.count(".json()") == 1
    assert ".then(readPredictResponse)" in page
    body = read_predict_response_body(page)
    assert body.index("'Content-Type'") < body.index("response.json()")


def test_non_json_413_shows_the_upload_size_message(webapp_module, client):
    body = read_predict_response_body(render_page(client))

    expected = json.dumps(webapp_module.UPLOAD_TOO_LARGE_MESSAGE)
    assert re.search(
        r"if \(response\.status === 413\) \{\s*return \{ error: "
        + re.escape(expected)
        + r" \};",
        body,
    )
