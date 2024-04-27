from src.app.functions.jcampdx import handler


def test_handler():
    event = {"foo": "bar"}
    context = None
    response = handler(event, context)

    assert response["statusCode"] == 200
    assert "body" in response
