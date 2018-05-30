from ssapi import create_app


def test_config():
    assert create_app().testing
