import io
import tempfile

import pytest
from PIL import Image

SECRET = "/internal/path/secret-detail"


@pytest.fixture
def class_names():
    return ["a", "b", "c", "d", "e"]


@pytest.fixture
def loaded_model(webapp_module, monkeypatch, stub_model, class_names):
    monkeypatch.setattr(webapp_module, "model", stub_model)
    monkeypatch.setattr(webapp_module, "class_names", class_names)
    monkeypatch.setattr(webapp_module, "transform", webapp_module.get_transform())
    monkeypatch.setattr(webapp_module, "device", "cpu")


def image_bytes(image_format, size=(8, 8)):
    buffer = io.BytesIO()
    Image.new("RGB", size).save(buffer, format=image_format)
    return buffer.getvalue()


def upload(client, data, filename="image.png"):
    return client.post(
        "/predict",
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


@pytest.mark.usefixtures("loaded_model")
@pytest.mark.parametrize(
    ("image_format", "extension"),
    [("PNG", "png"), ("JPEG", "jpg"), ("GIF", "gif"), ("BMP", "bmp")],
)
def test_predicts_each_allowed_format(client, image_format, extension):
    response = upload(client, image_bytes(image_format), f"image.{extension}")

    assert response.status_code == 200
    assert len(response.get_json()["predictions"]) == 5


@pytest.mark.usefixtures("loaded_model")
def test_predicts_upload_spooled_to_disk(client):
    large_upload = image_bytes("BMP", size=(512, 512))
    assert len(large_upload) > 500 * 1024

    response = upload(client, large_upload, "image.bmp")

    assert response.status_code == 200


@pytest.mark.usefixtures("loaded_model")
def test_prediction_does_not_use_a_named_temp_file(client, monkeypatch):
    def fail_like_windows(*_args, **_kwargs):
        raise PermissionError("named temp file reopened while still open")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fail_like_windows)

    response = upload(client, image_bytes("PNG"))

    assert response.status_code == 200


@pytest.mark.usefixtures("loaded_model")
def test_prediction_error_is_logged_but_not_returned(
    webapp_module, client, monkeypatch, caplog
):
    def raise_secret(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(webapp_module, "predict_image", raise_secret)

    response = upload(client, image_bytes("PNG"))

    assert response.status_code == 500
    assert response.get_json() == {"error": "Prediction failed"}
    assert SECRET not in response.get_data(as_text=True)
    assert SECRET in caplog.text


@pytest.mark.usefixtures("loaded_model")
@pytest.mark.parametrize(
    "data",
    [b"not an image", image_bytes("TIFF"), image_bytes("PNG")[:40]],
    ids=["text", "disallowed-format", "truncated"],
)
def test_unreadable_upload_is_a_client_error(client, data):
    response = upload(client, data)

    assert response.status_code == 400
    assert response.get_json() == {"error": "File could not be read as an image"}


@pytest.mark.usefixtures("loaded_model")
def test_image_above_the_pixel_limit_is_rejected_before_decoding(
    webapp_module, client, monkeypatch
):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("oversized image reached predict_image")

    monkeypatch.setattr(webapp_module, "MAX_UPLOAD_PIXELS", 63)
    monkeypatch.setattr(webapp_module, "predict_image", fail_if_called)

    response = upload(client, image_bytes("PNG"))

    assert response.status_code == 413
    assert response.get_json() == {"error": "Image dimensions are too large"}


@pytest.mark.usefixtures("loaded_model")
def test_image_at_the_pixel_limit_is_accepted(webapp_module, client, monkeypatch):
    monkeypatch.setattr(webapp_module, "MAX_UPLOAD_PIXELS", 64)

    assert upload(client, image_bytes("PNG")).status_code == 200


@pytest.mark.usefixtures("loaded_model")
def test_pil_decompression_bomb_error_is_rejected(client, monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)

    response = upload(client, image_bytes("PNG"))

    assert response.status_code == 413


@pytest.mark.usefixtures("loaded_model")
def test_upload_truncated_after_its_header_is_a_client_error(client, caplog):
    buffer = io.BytesIO()
    Image.effect_noise((64, 64), 50).save(buffer, format="PNG")
    truncated = buffer.getvalue()[: buffer.tell() // 2]

    response = upload(client, truncated)

    assert response.status_code == 400
    assert response.get_json() == {"error": "File could not be read as an image"}
    assert "Could not decode upload" in caplog.text
