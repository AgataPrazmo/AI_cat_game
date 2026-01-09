### Gra fabularna oparta na technologiach Kivy i FastAPI z wykorzystaniem OpenAI i metody Prompt Engineering do dynamicznej rozbudowy fabuły
Hybrydowy system narracyjny łączący statyczne drzewa decyzyjne z dynamiczną generacją treści przez OpenAI GPT. Aplikacja mobilna zbudowana w Kivy (Python) komunikująca się z asynchronicznym backendem FastAPI.

### Główne Funkcje
- Hybrydowa narracja: Połączenie predefiniowanych ścieżek z dynamicznym AI.
- Persystencja SQLite: Automatyczny zapis i unikalność promptów użytkowników.
- Blokada UI: Zabezpieczenie przed wielokrotnym wysyłaniem żądań (async/threading).
- System powrotów: Automatyczne wykrywanie węzłów końcowych i powrót do menu.

### Stos Technologiczny
- Frontend: Kivy
- Backend: FastAPI, Uvicorn
- Baza danych: SQLite
- Testy: Pytest (pełne pokrycie frontendu i backendu)

### Instalacja i Uruchomienie
1. Instalacja zależności:
```bash
pip install -r requirements.txt
```

2. Start Backend (FastAPI):
```bash
cd gra-backend
source venv/bin/activate
uvicorn main:app --reload
```

Start Frontend (Kivy):
```bash
cd gra-kivy
python main_app.py
```

### Testowanie
System zawiera pakiet testów automatycznych weryfikujących logikę biznesową, nawigację oraz odporność sieciową.
```bash
pytest gra-backend/test_backend.py
```
```bash
pytest gra-kivy/test_frontend.py
```

### Struktura Projektu
```bash
./PROJEKT-GRY
├── gra-backend
│   ├── static
│   ├── templates
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── shop.html
│   │   └── welcome.html
│   ├── main.py
│   ├── historie.py
│   ├── stories.db
│   └── test_backend.py
├── gra-kivy
│   ├── main.py
│   ├── config.py
│   ├── game.kv
│   ├── historie.py
│   ├── stories.db
│   └── test_frontend.py
├── requirements.txt
└── README.md
```
