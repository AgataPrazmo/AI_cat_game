# gra-backend/main.py

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
from openai import OpenAI
import os
import sqlite3
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from fastapi import HTTPException
import traceback
load_dotenv()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="supersecret")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
conn = sqlite3.connect("stories.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    story TEXT,
    node TEXT,
    prompt_text TEXT
)
""")
conn.commit()
conn.close()
users_db = {}
purchases = {}
conversation_history = {}


class User(BaseModel):
    username: str
    password: str


@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login-form", response_class=HTMLResponse)
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user or user["password"] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Błędny login lub hasło"})
    request.session["user"] = username
    return RedirectResponse("/shop", status_code=302)


@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Użytkownik już istnieje"})
    users_db[username] = {"password": password}
    purchases[username] = {"animations": False, "snacks": 0}
    request.session["user"] = username
    return RedirectResponse("/shop", status_code=302)


@app.get("/shop", response_class=HTMLResponse)
async def show_shop(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=302)
    user_purchases = purchases.get(user)
    if user_purchases is None:
        user_purchases = {"animations": False, "snacks": 0}
        purchases[user] = user_purchases
    return templates.TemplateResponse(
        "shop.html",
        {
            "request": request,
            "user": user,
            "purchases": user_purchases,
        },
    )


@app.get("/api/shop/{username}")
async def api_show_shop(username: str):
    user_purchases = purchases.get(username)
    if user_purchases is None:
        user_purchases = {"animations": False, "snacks": 0}
        purchases[username] = user_purchases
    return {"username": username, "purchases": user_purchases}


@app.post("/buy")
async def buy(request: Request, item: str = Form(...)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=302)
    if item == "animations":
        purchases[user]["animations"] = True
    elif item == "snacks":
        purchases[user]["snacks"] += 10
    return RedirectResponse("/shop", status_code=302)


@app.get("/me")
async def get_my_profile(request: Request):
    user = request.session.get("user")
    if not user:
        return {"error": "Not logged in"}
    return purchases[user]


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/api/register")
async def register_api(user: User):
    if user.username in users_db:
        return JSONResponse({"detail": "User already exists"}, status_code=400)
    users_db[user.username] = {"password": user.password}
    purchases[user.username] = {"animations": False, "snacks": 0}
    return {"message": "Registered successfully"}


@app.post("/api/login")
async def login_api(user: User):
    existing = users_db.get(user.username)
    if not existing or existing["password"] != user.password:
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
    return {"message": "Logged in successfully"}


@app.post("/api/choice")
async def choice_api(data: dict):
    story_title = data.get("story", "") 
    path = data.get("path", [])
    new_choice = data.get("new_choice", "")
    user = data.get("user", "unknown_user")
    
    if user not in conversation_history:
        conversation_history[user] = []
    
    print(f"\n--- DEBUG START ---")
    print(f"Użytkownik: {user}")
    print(f"Wybrana historia: '{story_title}'")
    print(f"Ścieżka wyborów (path): {path}")
    print(f"Nowa akcja gracza: '{new_choice}'")

    previous_text = ""

    try:
        from historie import historie
        if story_title in historie:
            node = historie[story_title]
            print(f" -> Pomyślnie wejści do historii: {story_title}")
        else:
            if path and path[0] in historie:
                story_title = path[0]
                node = historie[story_title]
                path = path[1:]
                print(f" -> Naprawiono: Tytuł wyciągnięty ze ścieżki: {story_title}")
            else:
                raise Exception(f"Nie znaleziono historii o tytule: '{story_title}'")
                
        for step_index, key in enumerate(path):
            print(f"Krok {step_index}: Szukam klucza '{key}'")
            
            if "choices" in node and key in node["choices"]:
                node = node["choices"][key]
                print(f" -> OK.")
            else:
                print(f"!!! OSTRZEŻENIE: Nie znaleziono wyboru '{key}'. Zatrzymuję się w ostatnim znanym miejscu.")
                break 

        previous_text = node.get("text") or node.get("intro") or ""
        
        if not previous_text:
            raise Exception("Znaleziono węzeł, ale brakuje w nim pola 'text' lub 'intro'!")

        print(f"SUKCES: Kontekst dla AI: {previous_text[:50]}...") 

    except Exception as e:
        print(f"BŁĄD w pętli historii: {e}")
        traceback.print_exc()
        previous_text = "Nie udało się ustalić miejsca akcji. Zakładamy, że jesteś w bezpiecznym, przytulnym miejscu."

    history_blocks = []
    if user in conversation_history:
        for turn in conversation_history[user]:
            history_blocks.append(f"Gracz: {turn['user']} -> Wynik: {turn['ai']}")
    recent_history = "\n".join(history_blocks[-3:])

    prompt = f"""

Oto fragment historii, który należy bezpośrednio kontynuować:
{previous_text}
{recent_history}
Ostatnia akcja kotka:
"{new_choice}"

Napisz 2–3 zdania będące naturalną kontynuacją tej samej sceny, PRZEDE WSZYSTKIM z uwzględnieniem ostatniej akcji.
Nie zmieniaj miejsca akcji i nie dodawaj nowych elementów,
jeśli nie wynikają one wprost z powyższego fragmentu.
Zachowaj realistyczne zachowanie prawdziwego kota
i ciepły, spokojny ton opowieści.
Pamiętaj o byciu family-friendly.
"""
    
    print(f"--- DEBUG END ---\n")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6 
        )
        story = response.choices[0].message.content
        
        conversation_history[user].append({
            "user": new_choice,
            "ai": story
        })

        return {"story": story}

    except Exception as e:
        print(f"Błąd OpenAI: {e}")
        return {"error": "Błąd generowania."}


@app.post("/api/reset_history")
async def reset_history(data: dict):
    user = data.get("user")
    if user in conversation_history:
        del conversation_history[user]
    return {"message": "History cleared"}


@app.post("/api/prompt")
async def save_prompt(data: dict):
    user = data.get("user")
    story = data.get("story")
    node = data.get("node")
    prompt_text = data.get("prompt_text")
    conn = sqlite3.connect("stories.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM prompts WHERE user=? AND story=? AND node=? AND prompt_text=?",
              (user, story, node, prompt_text))
    exists = c.fetchone()
    if not exists:
        c.execute("INSERT INTO prompts (user, story, node, prompt_text) VALUES (?, ?, ?, ?)",
                  (user, story, node, prompt_text))
        conn.commit()
    conn.commit()
    conn.close()
    return {"message": "Prompt saved"}


@app.get("/api/prompts/{user}/{story}/{node}")
async def get_prompts(user: str, story: str, node: str):
    conn = sqlite3.connect("stories.db")
    c = conn.cursor()
    c.execute("SELECT prompt_text FROM prompts WHERE user=? AND story=? AND node=?", (user, story, node))
    prompts = [row[0] for row in c.fetchall()]
    conn.close()
    return {"prompts": prompts}


@app.post("/api/buy")
async def api_buy(data: dict = Body(...)):
    username = data.get("username")
    item = data.get("item")
    if username not in purchases:
        return JSONResponse({"detail": "User not found"}, status_code=404)
    if item == "animations":
        purchases[username]["animations"] = True
    elif item == "snacks":
        purchases[username]["snacks"] += 10
    else:
        return JSONResponse({"detail": "Invalid item"}, status_code=400)
    return {"message": f"Bought {item}", "purchases": purchases[username]}


