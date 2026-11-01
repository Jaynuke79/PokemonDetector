import importlib.util
import io
import json
from pathlib import Path

import pytest
from PIL import Image

DEMO_DIR = Path(__file__).resolve().parents[1] / "demo-vercel"
API_PATH = DEMO_DIR / "api" / "index.py"
VALID_REPLY = json.dumps({"predictions": [{"pokemon": "Pikachu", "confidence": 0.9}]})
IMAGE_PAYLOAD = {"image": "data:image/png;base64,AAAA"}
PARSE_ERROR = [
    {
        "class_name": "Parsing Error - See Console",
        "confidence": "0.0000",
        "percentage": "0.00%",
    }
]


class FakeResponse:
    status_code = 200

    def __init__(self, content):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


@pytest.fixture
def vercel_api(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    spec = importlib.util.spec_from_file_location("vercel_api", API_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def predict_with_content(vercel_api, monkeypatch):
    def predict(content):
        def fake_post(*_args, **_kwargs):
            return FakeResponse(content)

        monkeypatch.setattr(vercel_api.requests, "post", fake_post)
        return vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)

    return predict


@pytest.fixture
def predict_with_reply(predict_with_content):
    def predict(model_reply):
        return predict_with_content(
            model_reply if isinstance(model_reply, str) else json.dumps(model_reply)
        )

    return predict


def test_numeric_confidences_are_formatted(predict_with_reply):
    response = predict_with_reply(
        {
            "predictions": [
                {"pokemon": "Gengar", "confidence": 0.95},
                {"pokemon": "Haunter", "confidence": 0.05},
            ]
        }
    )

    assert response.status_code == 200
    assert response.get_json()["predictions"] == [
        {"class_name": "Gengar", "confidence": "0.9500", "percentage": "95.00%"},
        {"class_name": "Haunter", "confidence": "0.0500", "percentage": "5.00%"},
    ]


def test_numeric_string_confidence_is_coerced(predict_with_reply):
    response = predict_with_reply(
        {"predictions": [{"pokemon": "Pikachu", "confidence": "0.9"}]}
    )

    assert response.status_code == 200
    assert response.get_json()["predictions"] == [
        {"class_name": "Pikachu", "confidence": "0.9000", "percentage": "90.00%"}
    ]


@pytest.mark.parametrize("confidence", ["high", None, "nan", "inf", [0.9]])
def test_unusable_confidence_becomes_zero(predict_with_reply, confidence):
    response = predict_with_reply(
        {"predictions": [{"pokemon": "Pikachu", "confidence": confidence}]}
    )

    assert response.status_code == 200
    assert response.get_json()["predictions"] == [
        {"class_name": "Pikachu", "confidence": "0.0000", "percentage": "0.00%"}
    ]


def test_missing_confidence_becomes_zero(predict_with_reply):
    response = predict_with_reply({"predictions": [{"pokemon": "Pikachu"}]})

    assert response.status_code == 200
    assert response.get_json()["predictions"] == [
        {"class_name": "Pikachu", "confidence": "0.0000", "percentage": "0.00%"}
    ]


def test_non_dict_entries_are_skipped(predict_with_reply):
    response = predict_with_reply(
        {
            "predictions": [
                "Pikachu",
                {"pokemon": "Raichu", "confidence": 0.5},
                42,
            ]
        }
    )

    assert response.status_code == 200
    assert response.get_json()["predictions"] == [
        {"class_name": "Raichu", "confidence": "0.5000", "percentage": "50.00%"}
    ]


@pytest.mark.parametrize(
    "model_reply",
    [
        {"predictions": ["Pikachu", "Raichu"]},
        {"predictions": "Pikachu"},
        {"predictions": {"pokemon": "Pikachu", "confidence": 0.9}},
        {"predictions": []},
        {"pokemon": "Pikachu"},
        [{"pokemon": "Pikachu", "confidence": 0.9}],
        "not json at all",
    ],
)
def test_bad_shape_returns_parse_error_fallback(predict_with_reply, model_reply):
    response = predict_with_reply(model_reply)

    assert response.status_code == 200
    assert response.get_json()["predictions"] == PARSE_ERROR


@pytest.mark.parametrize("content", [None, [{"type": "text", "text": "Pikachu"}]])
def test_non_text_content_returns_parse_error_fallback(predict_with_content, content):
    response = predict_with_content(content)

    assert response.status_code == 200
    assert response.get_json()["predictions"] == PARSE_ERROR


@pytest.mark.parametrize("confidence", [0.91234, 0.00005, 1.0, 0.0])
def test_backends_format_predictions_identically(
    vercel_api, webapp_module, client, monkeypatch, confidence
):
    upload = io.BytesIO()
    Image.new("RGB", (8, 8)).save(upload, format="PNG")
    upload.seek(0)
    monkeypatch.setattr(webapp_module, "model", object())
    monkeypatch.setattr(
        webapp_module,
        "predict_image",
        lambda *_args, **_kwargs: [(0, "Gengar", confidence)],
    )

    webapp_predictions = client.post(
        "/predict",
        data={"file": (upload, "image.png")},
        content_type="multipart/form-data",
    ).get_json()["predictions"]
    demo_predictions = vercel_api.format_predictions(
        {"predictions": [{"pokemon": "Gengar", "confidence": confidence}]}, topk=1
    )

    assert webapp_predictions == demo_predictions, (
        "Prediction formatting differs between webapp/app.py and "
        "demo-vercel/api/index.py. The two copies are kept on purpose: apply the "
        "same edit to both."
    )


@pytest.fixture
def post_image(vercel_api, monkeypatch):
    forwarded_image_urls = []

    def fake_post(*_args, **kwargs):
        content = kwargs["json"]["messages"][0]["content"]
        forwarded_image_urls.append(content[1]["image_url"]["url"])
        return FakeResponse(VALID_REPLY)

    monkeypatch.setattr(vercel_api.requests, "post", fake_post)

    def post(image):
        response = vercel_api.app.test_client().post(
            "/api/predict", json={"image": image}
        )
        return response, forwarded_image_urls

    return post


@pytest.mark.parametrize(
    "image",
    [
        "data:text/plain;base64,AAAA",
        "data:application/pdf;base64,AAAA",
        "data:text/html,<b>hi</b>",
        "data:image/svg+xml;base64,AAAA",
        "data:image/bmp;base64,AAAA",
        "data:;base64,AAAA",
        "data:image/png;base64",
        "DATA:text/plain;base64,AAAA",
        "Data:application/pdf;base64,AAAA",
        " data:text/plain;base64,AAAA",
    ],
)
def test_disallowed_image_type_is_rejected_before_calling_upstream(post_image, image):
    response, forwarded_image_urls = post_image(image)

    assert response.status_code == 400
    assert "Unsupported image type" in response.get_json()["error"]
    assert forwarded_image_urls == []


@pytest.mark.parametrize(
    ("image", "forwarded"),
    [
        ("data:image/png;base64,AAAA", "data:image/png;base64,AAAA"),
        ("data:image/jpeg;base64,AAAA", "data:image/jpeg;base64,AAAA"),
        ("data:image/gif;base64,AAAA", "data:image/gif;base64,AAAA"),
        ("data:image/webp;base64,AAAA", "data:image/webp;base64,AAAA"),
        ("data:IMAGE/PNG;base64,AAAA", "data:image/png;base64,AAAA"),
        ("DATA:image/png;base64,AAAA", "data:image/png;base64,AAAA"),
        (" data:image/png;base64,AAAA\n", "data:image/png;base64,AAAA"),
        ("AAAA", "data:image/jpeg;base64,AAAA"),
    ],
)
def test_allowed_image_type_is_forwarded(post_image, image, forwarded):
    response, forwarded_image_urls = post_image(image)

    assert response.status_code == 200
    assert forwarded_image_urls == [forwarded]


@pytest.mark.parametrize(
    "image",
    [
        "plain text not base64",
        "",
        "   ",
        "AAA",
        "pikachu\u20ac",
        "data:image/png,not base64 <b>",
        "data:image/png;base64,",
        "data:image/png;base64,not base64",
    ],
)
def test_invalid_base64_is_rejected_before_calling_upstream(post_image, image):
    response, forwarded_image_urls = post_image(image)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Image data is not valid base64"
    assert forwarded_image_urls == []


@pytest.fixture
def timed_out_request(vercel_api, monkeypatch):
    upstream_timeouts = []
    sleeps = []

    def fake_post(*_args, **kwargs):
        upstream_timeouts.append(kwargs["timeout"])
        raise vercel_api.requests.exceptions.Timeout

    monkeypatch.setattr(vercel_api.requests, "post", fake_post)
    monkeypatch.setattr("time.sleep", sleeps.append)
    response = vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)
    return response, upstream_timeouts, sleeps


def test_worst_case_upstream_time_fits_function_duration(timed_out_request):
    _, upstream_timeouts, sleeps = timed_out_request
    config = json.loads((DEMO_DIR / "vercel.json").read_text())
    max_duration = config["functions"]["api/index.py"]["maxDuration"]

    connect_and_read_seconds = sum(sum(timeout) for timeout in upstream_timeouts)

    assert connect_and_read_seconds + sum(sleeps) < max_duration


def test_timeout_error_hides_model_and_limits(vercel_api, timed_out_request, caplog):
    response, _, _ = timed_out_request

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "The model took too long to respond. Try a smaller image."
    }
    assert any(
        vercel_api.OPENROUTER_MODEL in str(record.exc_info[1])
        for record in caplog.get_records("setup")
    )


def test_vercel_config_does_not_combine_builds_with_functions():
    config = json.loads((DEMO_DIR / "vercel.json").read_text())

    assert "builds" not in config


UPSTREAM_DETAIL = "https://openrouter.ai/api/v1/chat/completions upstream-detail"


def raise_from_post(exception):
    def fake_post(*_args, **_kwargs):
        raise exception

    return fake_post


def reply_with_envelope(envelope):
    class EnvelopeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return envelope

    def fake_post(*_args, **_kwargs):
        return EnvelopeResponse()

    return fake_post


@pytest.mark.parametrize(
    "make_fake_post",
    [
        lambda api: raise_from_post(
            api.requests.exceptions.HTTPError(f"404 Client Error for {UPSTREAM_DETAIL}")
        ),
        lambda api: raise_from_post(
            api.requests.exceptions.ConnectionError(UPSTREAM_DETAIL)
        ),
        lambda api: raise_from_post(RuntimeError(UPSTREAM_DETAIL)),
        lambda _api: reply_with_envelope({"error": UPSTREAM_DETAIL}),
    ],
    ids=["http-error", "connection-error", "unexpected-error", "no-choices"],
)
def test_upstream_failure_detail_is_logged_not_returned(
    vercel_api, monkeypatch, caplog, make_fake_post
):
    monkeypatch.setattr(vercel_api.requests, "post", make_fake_post(vercel_api))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    response = vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Prediction failed"}
    assert UPSTREAM_DETAIL in caplog.text


@pytest.mark.parametrize(
    ("envelope", "exception_text"),
    [
        ({"choices": [{}]}, "message"),
        ({"choices": None}, "NoneType"),
    ],
    ids=["choice-without-message", "null-choices"],
)
def test_malformed_envelope_returns_generic_error(
    vercel_api, monkeypatch, envelope, exception_text
):
    monkeypatch.setattr(vercel_api.requests, "post", reply_with_envelope(envelope))

    response = vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Prediction failed"}
    assert exception_text not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("request_kwargs", "status", "error"),
    [
        (
            {"data": "{not json", "content_type": "application/json"},
            400,
            "Bad Request",
        ),
        (
            {"data": "text", "content_type": "text/plain"},
            415,
            "Unsupported Media Type",
        ),
        (
            {"data": "x" * 5_000_000, "content_type": "application/json"},
            413,
            "Request Entity Too Large",
        ),
    ],
    ids=["invalid-json", "wrong-content-type", "too-large"],
)
def test_rejected_request_keeps_its_status_with_a_fixed_message(
    vercel_api, request_kwargs, status, error
):
    response = vercel_api.app.test_client().post("/api/predict", **request_kwargs)

    assert response.status_code == status
    assert response.get_json() == {"error": error}


def test_missing_api_key_message_stays_helpful(vercel_api, monkeypatch):
    monkeypatch.setattr(vercel_api, "OPENROUTER_API_KEY", None)

    response = vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)

    assert response.status_code == 500
    assert response.get_json() == {"error": "OpenRouter API key not configured"}


LIMIT_MESSAGE = "This demo has reached its daily limit. Please try again later."
LIMIT_DETAIL = "$1.02 of $1.00 used; resets 2026-10-12T00:00:00.000Z"


def openrouter_error(limit_source=None, code=402):
    metadata = {"limit_source": limit_source} if limit_source else {}
    return {"error": {"code": code, "message": LIMIT_DETAIL, "metadata": metadata}}


@pytest.fixture
def predict_with_upstream_status(vercel_api, monkeypatch):
    upstream_calls = []
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    def predict(status_code, content):
        def fake_post(*_args, **_kwargs):
            upstream_calls.append(1)
            response = vercel_api.requests.Response()
            response.status_code = status_code
            response._content = content
            return response

        monkeypatch.setattr(vercel_api.requests, "post", fake_post)
        response = vercel_api.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)
        return response, len(upstream_calls)

    return predict


@pytest.mark.parametrize("status_code", [402, 403])
@pytest.mark.parametrize(
    "limit_source",
    [
        "openrouter_key_limit",
        "openrouter_guardrail_budget",
        "openrouter_workspace_budget",
    ],
)
def test_spending_cap_returns_fixed_message_without_retrying(
    predict_with_upstream_status, caplog, limit_source, status_code
):
    body = openrouter_error(limit_source, status_code)

    response, upstream_calls = predict_with_upstream_status(
        status_code, json.dumps(body).encode()
    )

    assert response.status_code == 503
    assert response.get_json() == {"error": LIMIT_MESSAGE}
    assert upstream_calls == 1
    assert LIMIT_DETAIL in caplog.text


@pytest.mark.parametrize(
    ("status_code", "content"),
    [
        (402, json.dumps(openrouter_error("openrouter_credits")).encode()),
        (402, json.dumps(openrouter_error("openrouter_in_flight_budget")).encode()),
        (402, json.dumps(openrouter_error()).encode()),
        (403, json.dumps(openrouter_error()).encode()),
        (429, json.dumps(openrouter_error("openrouter_key_limit")).encode()),
        (402, b"not json"),
        (402, b"[]"),
        (402, b'{"error": "text"}'),
        (402, b'{"error": {"metadata": "text"}}'),
        (402, b'{"error": {"metadata": {"limit_source": ["openrouter_key_limit"]}}}'),
    ],
    ids=[
        "credits",
        "in-flight-budget",
        "402-no-source",
        "403-no-source",
        "key-source-on-429",
        "not-json",
        "not-object",
        "error-not-object",
        "metadata-not-object",
        "limit-source-not-string",
    ],
)
def test_other_upstream_errors_stay_generic_and_retry(
    predict_with_upstream_status, status_code, content
):
    response, upstream_calls = predict_with_upstream_status(status_code, content)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Prediction failed"}
    assert upstream_calls == 2


def test_api_key_with_trailing_newline_stays_out_of_logs(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-secret-key\n")
    spec = importlib.util.spec_from_file_location("vercel_api", API_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def send_prepared_request(_session, prepared, **_kwargs):
        assert prepared.headers["Authorization"] == "Bearer sk-or-secret-key"
        raise module.requests.exceptions.ConnectionError("upstream unavailable")

    monkeypatch.setattr(module.requests.Session, "send", send_prepared_request)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    response = module.app.test_client().post("/api/predict", json=IMAGE_PAYLOAD)

    assert response.get_json() == {"error": "Prediction failed"}
    assert "sk-or-secret-key" not in caplog.text
