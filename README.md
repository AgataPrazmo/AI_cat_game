### Role-playing game based on Kivy and FastAPI technologies using OpenAI and the Prompt Engineering method for dynamic plot expansion (Polish language model)
Hybrid narrative system combining static decision trees with dynamic content generation by OpenAI GPT. Mobile application built in Kivy (Python) communicating with an asynchronous FastAPI backend.

### Main Features
- Hybrid narrative: Combination of predefined paths with dynamic AI.
- SQLite persistence: Automatic saving and uniqueness of user prompts.
- UI lock: Protection against multiple request sending (async/threading).
- Return system: Automatic detection of terminal nodes and return to menu.

### Technology Stack
- Frontend: Kivy
- Backend: FastAPI, Uvicorn
- Database: SQLite
- Tests: Pytest (full coverage of frontend and backend)


### Environment Variables
For the application to function correctly, you must provide your own API keys. Never commit your .env file to version control.
1. Create a .env file in the gra-backend directory.
2. Add the following variables:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

The backend uses these variables to securely communicate with OpenAI and manage the SQLite database.

### Installation and Launch
1. Installation of dependencies:
```bash
pip install -r requirements.txt
```

2. Start Backend (FastAPI):
```bash
cd gra-backend
source venv/bin/activate
uvicorn main:app --reload
```

3. Start Frontend (Kivy):
```bash
cd gra-kivy
python main_app.py
```

### Testing
The system contains a package of automated tests verifying business logic, navigation, and network resilience.
```bash
pytest gra-backend/test_backend.py
```
```bash
pytest gra-kivy/test_frontend.py
```

### Project Structure
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
