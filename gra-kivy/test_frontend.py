import pytest
import os
import requests
from unittest.mock import patch, MagicMock

os.environ['KIVY_NO_ARGS'] = '1'

from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from main import GameApp, GameScreen


def test_screen_navigation():
    """
    Testy Nawigacji Ekranów:
    Weryfikacja dostępności ekranów logowania, rejestracji i gry.
    """
    app = GameApp()
    root = app.build()

    assert 'login' in root.screen_names
    assert 'register' in root.screen_names
    assert 'game' in root.screen_names

    app.current_user = "test_user"
    root.current = "game"
    assert root.current == "game"


@pytest.mark.parametrize("path", [
    ["Mruczek i nocna przygoda"],
    ["Mruczek i nocna przygoda", "Wskoczyć pod kołdrę"],
    ["Mruczek i nocna przygoda", "Wyjrzeć przez okno"],
])


def test_story_branch_exploration(path):
    """
    Testy Interpretacji Narracji:
    Eksploracja statycznych gałęzi fabularnych.
    """
    app = GameApp()
    app.current_user = "test_user"

    screen = GameScreen(name="game")
    screen.current_path = path

    screen.update_story()
    Clock.tick()

    assert screen.story_text is not None


def test_terminal_node_logic():
    """
    Testy Logiki Węzłów Końcowych:
    Weryfikacja, że po osiągnięciu węzła terminalnego
    nie są generowane dalsze opcje fabularne,
    a interfejs przechodzi w stan zakończenia historii.
    """
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"prompts": []}

        screen = GameScreen(name='game')
        screen.current_path = [
            "Mruczek i nocna przygoda",
            "Wskoczyć pod kołdrę",
            "Zwinąć się w kulkę"
        ]

        screen.update_story()
        Clock.tick()
        assert len(screen.ids.buttons_box.children) <= 1

def test_ui_locking_during_request():
    """
    Testy Responsywności UI:
    Weryfikacja, że UI reaguje natychmiast i nie jest blokowane.
    """
    app = GameApp()
    app.current_user = "test_user"
    screen = GameScreen(name="game")

    screen.ids.choice_input.text = "Testowy prompt"

    with patch('threading.Thread'), patch('requests.post'):
        screen.submit_choice()

        assert screen.ids.choice_input.disabled is True
        assert "Kotek myśli" in screen.story_text


def test_network_error_handling():
    """
    Testy Błędów Sieciowych:
    Weryfikacja odporności aplikacji na brak połączenia z backendem.
    """
    app = GameApp()
    app.current_user = "test_user"
    screen = GameScreen(name="game")

    with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
        screen.ids.choice_input.text = "Test"
        screen.submit_choice()
        assert screen.ids.choice_input.disabled is True


def test_saved_prompts_reuse():
    """
    Testy Mechanizmu Promptów Zapisanych:
    Weryfikacja renderowania zapisanych promptów z backendu (SQLite).
    """
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "prompts": ["Uciekaj stąd!"]
        }

        app = MagicMock(current_user="inzynier")
        with patch('kivy.app.App.get_running_app', return_value=app):
            screen = GameScreen()
            screen.current_path = ["Łatek i tajemniczy karton"]

            screen.update_story()

            button_texts = [
                btn.text for btn in screen.ids.buttons_box.children
            ]
            assert "Uciekaj stąd!" in button_texts

