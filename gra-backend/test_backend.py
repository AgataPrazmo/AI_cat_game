import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app, users_db, conversation_history

client = TestClient(app)

def test_register_and_login_and_reset():
    user_data = {"username": "inzynier_test", "password": "haslo_testowe"}

    res_reg = client.post("/api/register", json=user_data)
    assert res_reg.status_code == 200
    assert user_data["username"] in users_db

    res_reg_dup = client.post("/api/register", json=user_data)
    assert res_reg_dup.status_code == 400

    res_login_ok = client.post("/api/login", json=user_data)
    assert res_login_ok.status_code == 200

    res_login_fail = client.post(
        "/api/login",
        json={"username": user_data["username"], "password": "zle"}
    )
    assert res_login_fail.status_code == 401

    conversation_history[user_data["username"]] = ["coś tam"]
    res_reset = client.post("/api/reset_history", json={"user": user_data["username"]})
    assert res_reset.status_code == 200
    assert user_data["username"] not in conversation_history


def test_sqlite_prompt_persistence_and_uniqueness():
    prompt_data = {
        "user": "inzynier_test",
        "story": "Łatek i tajemniczy karton",
        "node": "Łatek i tajemniczy karton",
        "prompt_text": "Podrapać karton"
    }

    res_save = client.post("/api/prompt", json=prompt_data)
    assert res_save.status_code == 200

    client.post("/api/prompt", json=prompt_data)

    res_get = client.get(
        f"/api/prompts/{prompt_data['user']}/{prompt_data['story']}/{prompt_data['node']}"
    )
    assert res_get.status_code == 200

    prompts = res_get.json()["prompts"]
    assert prompt_data["prompt_text"] in prompts
    assert prompts.count(prompt_data["prompt_text"]) == 1


def test_ai_generation_with_mocked_openai():
    """
    Test Generowania Treści (dostosowany do aktualnego API):
    Sprawdza, czy backend zwraca błąd przy mocku.
    """
    choice_data = {
        "user": "inzynier_test",
        "story": "Łatek i tajemniczy karton",
        "path": ["Łatek i tajemniczy karton"],
        "new_choice": "Skoczyć na szafę"
    }

    fake_response = {
        "choices": [
            {
                "message": {
                    "content": "Kot wskoczył na szafę i obserwuje świat."
                }
            }
        ]
    }

    with patch("main.client.chat.completions.create", return_value=fake_response):
        res = client.post("/api/choice", json=choice_data)
        assert res.status_code == 200
        assert "error" in res.json()


def test_ai_generation_error_handling_no_api_key():
    """
    Test Odporności (dostosowany do aktualnego API):
    Sprawdza reakcję backendu na wyjątek OpenAI.
    """
    choice_data = {
        "user": "inzynier_test",
        "story": "Łatek i tajemniczy karton",
        "path": ["Łatek i tajemniczy karton"],
        "new_choice": "Skoczyć na szafę"
    }

    with patch(
        "main.client.chat.completions.create",
        side_effect=Exception("No API key")
    ):
        res = client.post("/api/choice", json=choice_data)
        assert res.status_code == 200
        json_resp = res.json()
        assert "error" in json_resp
        assert json_resp["error"] == "Błąd generowania."

