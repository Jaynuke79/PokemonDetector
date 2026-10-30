import importlib.util
import json
from pathlib import Path

import pytest

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


def test_timeout_error_describes_the_configured_limits(timed_out_request):
    response, upstream_timeouts, _ = timed_out_request
    error = response.get_json()["error"]

    assert f"after {len(upstream_timeouts)} attempts" in error
    assert f"{upstream_timeouts[0][1]}s per attempt" in error
    assert "10s limit" not in error
    assert "Vercel Pro" not in error


def test_vercel_config_does_not_combine_builds_with_functions():
    config = json.loads((DEMO_DIR / "vercel.json").read_text())

    assert "builds" not in config
