import importlib.util
import json
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "demo-vercel" / "api" / "index.py"
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
