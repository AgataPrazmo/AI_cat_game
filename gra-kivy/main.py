# gra-kivy/main.py

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.clock import Clock
import threading
import requests
from config import BASE_URL
from historie import historie


class RegisterScreen(Screen):
    def register(self):
        user = self.ids.reg_user.text.strip()
        pw = self.ids.reg_pass.text.strip()
        if not user or not pw:
            self.ids.reg_msg.text = "Podaj login i hasło."
            return
        self.ids.reg_msg.text = "Rejestruję, chwilka..."
        def do_request():
            try:
                res = requests.post(
                    f"{BASE_URL}/api/register",
                    json={"username": user, "password": pw}
                )
                if res.status_code == 200:
                    def on_success(dt):
                        App.get_running_app().current_user = user
                        self.manager.current = "game"
                    Clock.schedule_once(on_success, 0)
                else:
                    msg = res.json().get("detail", "Błąd rejestracji.")
                    Clock.schedule_once(lambda dt: setattr(self.ids.reg_msg, "text", msg), 0)
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: setattr(self.ids.reg_msg, "text", f"Błąd połączenia: {e}"),
                    0
                )
        threading.Thread(target=do_request, daemon=True).start()


class LoginScreen(Screen):
    def login(self):
        user = self.ids.log_user.text.strip()
        pw = self.ids.log_pass.text.strip()
        if not user or not pw:
            self.ids.log_msg.text = "Podaj login i hasło."
            return
        self.ids.log_msg.text = "Loguję, chwilka..."
        def do_request():
            try:
                res = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": user, "password": pw}
                )
                if res.status_code == 200:
                    def on_success(dt):
                        App.get_running_app().current_user = user
                        self.manager.current = "game"
                    Clock.schedule_once(on_success, 0)
                else:
                    msg = res.json().get("detail", "Błąd logowania.")
                    Clock.schedule_once(lambda dt: setattr(self.ids.log_msg, "text", msg), 0)
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: setattr(self.ids.log_msg, "text", f"Błąd połączenia: {e}"),
                    0
                )
        threading.Thread(target=do_request, daemon=True).start()


class GameScreen(Screen):
    story_text = StringProperty("")
    current_path = ListProperty([])

    def on_pre_enter(self):
        app = App.get_running_app()
        if not getattr(app, "current_user", None):
            self.manager.current = "login"
            return
        self.show_story_selection()
        
    def show_story_selection(self):
        app = App.get_running_app()
        user = getattr(app, "current_user", None)
        if user:
            try:
                requests.post(f"{BASE_URL}/api/reset_history", json={"user": user})
            except Exception as e:
                print("Błąd resetu historii:", e)
        self.story_text = "Wybierz przygodę kotka:"
        self.current_path = []
        self.ids.buttons_box.clear_widgets()
        for title in historie.keys():
            btn = Button(text=title, size_hint_y=None, height=40)
            btn.bind(on_release=lambda instance, t=title: self.select_story(t))
            self.ids.buttons_box.add_widget(btn)
        self.ids.choice_input.text = ""
        self.ids.choice_input.opacity = 0
        self.ids.choice_input.disabled = True

    def select_story(self, title):
        self.current_path = [title]
        self.update_story()

    def choose_option(self, choice):
        self.current_path.append(choice)
        self.update_story()

    def use_saved_prompt(self, prompt_text):
        """Użyj zapisanego prompta tak, jakby gracz wpisał go ręcznie."""
        self.ids.choice_input.text = prompt_text
        self.submit_choice()

    def update_story(self):
        node = historie
        for key in self.current_path:
            if "choices" in node:
                node = node["choices"].get(key, {})
            else:
                node = node.get(key, {})
        text = node.get("text") or node.get("intro", "Koniec :)")
        self.story_text = text
        self.ids.buttons_box.clear_widgets()
        children = node.get("choices")
        if children:
            for choice_text in children.keys():
                btn = Button(text=choice_text, size_hint_y=None, height=40)
                btn.bind(on_release=lambda instance, c=choice_text: self.choose_option(c))
                self.ids.buttons_box.add_widget(btn)
            try:
                user = App.get_running_app().current_user
                story = self.current_path[0] if self.current_path else "unknown"
                node_key = " > ".join(self.current_path) if self.current_path else "start"

                res = requests.get(f"{BASE_URL}/api/prompts/{user}/{story}/{node_key}")
                if res.status_code == 200:
                    prompts = res.json().get("prompts", [])
                    for prompt_text in prompts:
                        btn = Button(text=prompt_text, size_hint_y=None, height=40)
                        btn.bind(on_release=lambda instance, p=prompt_text: self.use_saved_prompt(p))
                        self.ids.buttons_box.add_widget(btn)
            except Exception as e:
                print("Błąd pobierania promptów:", e)
            self.ids.choice_input.text = ""
            self.ids.choice_input.opacity = 1
            self.ids.choice_input.disabled = False
        else:
            btn = Button(text="Wróć do menu", size_hint_y=None, height=40)
            btn.bind(on_release=lambda instance: self.show_story_selection())
            self.ids.buttons_box.add_widget(btn)
            self.ids.choice_input.text = ""
            self.ids.choice_input.opacity = 0
            self.ids.choice_input.disabled = True

    def submit_choice(self):
        app = App.get_running_app()
        user = getattr(app, "current_user", None)
        user_input = self.ids.choice_input.text.strip()
        if not user:
            self.story_text = "Najpierw się zaloguj."
            return
        if not user_input:
            return
        self.ids.choice_input.text = ""
        self.story_text = "Kotek myśli nad Twoją odpowiedzią..."
        self.ids.choice_input.disabled = True
        current_path_snapshot = list(self.current_path)
        def do_request():
            try:
                res = requests.post(
                    f"{BASE_URL}/api/choice",
                    json=
                    {
                        "user": user,
                        "path": current_path_snapshot,
                        "new_choice": user_input
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    story_text = data.get("story", "Brak odpowiedzi AI.")
                    story = current_path_snapshot[0] if current_path_snapshot else "unknown"
                    node_key =(
                        " > ".join(current_path_snapshot)
                        if current_path_snapshot else "start"
                    )
                    try:
                        res2 = requests.post(
                            f"{BASE_URL}/api/prompt",
                            json=
                            {
                                "user": user,
                                "story": story,
                                "node": node_key,
                                "prompt_text": user_input
                            }
                        )
                        if res2.status_code != 200:
                            print("Błąd zapisu prompta:", res2.text)
                    except Exception as e2:
                        print("Błąd zapisu prompta:", e2)
                    def on_success(dt):
                        self.story_text = story_text
                        self.current_path = current_path_snapshot + [user_input]
                        self.ids.buttons_box.clear_widgets()
                        btn = Button(
                            text="Wróć do menu",
                            size_hint_y=None,
                            height=40
                        )
                        btn.bind(on_release=lambda instance: self.show_story_selection())
                        self.ids.buttons_box.add_widget(btn)
                    Clock.schedule_once(on_success, 0)
                else:
                    Clock.schedule_once(
                        lambda dt: setattr(self, "story_text", "Błąd generowania historii."),
                        0
                    )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: setattr(self, "story_text", f"Błąd połączenia: {e}"),
                    0
                )
            finally:
                def unlock(dt):
                    self.ids.choice_input.disabled = False
                Clock.schedule_once(unlock, 0)
        threading.Thread(target=do_request, daemon=True).start()


class GameApp(App):
    def build(self):
        self.current_user = None  
        return Builder.load_file("game.kv")


if __name__ == "__main__":
    GameApp().run()

