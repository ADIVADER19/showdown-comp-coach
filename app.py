import os
import json
import logging
import requests
import nest_asyncio
from bson.objectid import ObjectId
from datetime import datetime
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from google.genai import types

# --- ADK Imports ---
try:
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.runners import InMemoryRunner
except Exception:
    pass 

# --- App Config ---
nest_asyncio.apply()
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_default_secret_key')
bcrypt = Bcrypt(app)

# --- Database Setup ---
mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/pokemon_coach")
try:
    client = MongoClient(mongo_uri)
    db = client.get_database('pokemon_coach') 
    users_collection = db.users
    print("✅ MongoDB Connected")
except Exception as e:
    print(f"❌ DB Error: {e}")

# --- Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = str(user_dict['_id'])
        self.username = user_dict['username']
        self.knowledge_level = user_dict.get('knowledge_level', 'Beginner')

    @staticmethod
    def get(user_id):
        try:
            if not ObjectId.is_valid(user_id): return None
            data = users_collection.find_one({"_id": ObjectId(user_id)})
            return User(data) if data else None
        except: return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- AI Setup ---
APP_NAME = "agents"
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: raise ValueError("Key missing")
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
except Exception as e:
    print(f"API Key Warning: {e}")

# --- Tools ---
def get_usage_stats(format: str) -> str:
    clean_format = format.lower().strip().replace(" ", "")
    if "gen9ou" in clean_format: clean_format = "gen9ou"
    url = f"https://data.pkmn.cc/stats/{clean_format}.json"
    try:
        response = requests.get(url); response.raise_for_status()
        data = response.json(); top_20 = list(data.keys())[:20]
        return f"Top 20 Usage: {', '.join(top_20)}"
    except: return f"Stats not found for {clean_format}."

def get_sample_teams(format: str) -> str:
    clean_format = format.lower().strip().replace(" ", "")
    url = f"https://data.pkmn.cc/teams/{clean_format}.json"
    try:
        response = requests.get(url); response.raise_for_status()
        return f"Sample Teams: {json.dumps(response.json()[:2])}"
    except: return f"No samples for {clean_format}."

# --- System Prompt ---
def get_system_prompt(knowledge_level):
    base_prompt = """You are 'Rotom-Coach', a Grandmaster Pokemon Coach.
    **Directives:**
    1. Ask for Format if missing.
    2. Use `get_usage_stats` for data.
    3. OUTPUT TEAMS IN SHOWDOWN IMPORTABLE FORMAT INSIDE CODE BLOCKS (```).
    """
    if knowledge_level == 'Beginner': base_prompt += "Explain terms (STAB, EVs). Be educational."
    elif knowledge_level == 'Expert': base_prompt += "Be concise. Focus on calcs and win-cons."
    return base_prompt

# --- Runner ---
RUNNER_CACHE = {} 
INITIALIZED_SESSIONS = set() # Keeps track of active sessions

def get_runner(session_id, user_level):
    if session_id in RUNNER_CACHE:
        return RUNNER_CACHE[session_id]

    retry = types.HttpRetryOptions(attempts=3)
    model = Gemini(model="models/gemini-2.5-pro", retry_options=retry)
    
    agent = LlmAgent(
        name="coach", 
        model=model, 
        instruction=get_system_prompt(user_level), 
        tools=[get_usage_stats, get_sample_teams]
    )
    
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    RUNNER_CACHE[session_id] = runner
    return runner

# --- Routes ---
@app.route('/')
def landing(): return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if users_collection.find_one({"username": request.form['username']}):
            flash('Username taken.')
            return redirect(url_for('register'))
        
        hashed = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        users_collection.insert_one({
            "username": request.form['username'], 
            "password": hashed,
            "knowledge_level": request.form['level'], 
            "created_at": datetime.utcnow(),
            "teams": [] 
        })
        login_user(User(users_collection.find_one({"username": request.form['username']})))
        return redirect(url_for('chat_app'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users_collection.find_one({"username": request.form['username']})
        if user and bcrypt.check_password_hash(user['password'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('chat_app'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('landing'))

@app.route('/app')
@login_required
def chat_app(): return render_template('chat.html', user=current_user)

@app.route('/profile')
@login_required
def profile():
    user_data = users_collection.find_one({"_id": ObjectId(current_user.id)})
    teams = user_data.get('teams', [])
    teams.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
    return render_template('profile.html', user=current_user, teams=teams)

@app.route('/save_team', methods=['POST'])
@login_required
def save_team():
    data = request.json
    new_team = {
        "_id": str(ObjectId()), 
        "title": data.get('title', 'Untitled'),
        "format": data.get('format', 'Unknown'),
        "team_data": data.get('team_text'),
        "date": datetime.utcnow()
    }
    users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$push": {"teams": new_team}}
    )
    return jsonify({"status": "success"})

@app.route('/chat', methods=['POST'])
@login_required
async def chat():
    msg = request.json.get('message')
    session_id = f"session_{current_user.id}"
    runner = get_runner(session_id, current_user.knowledge_level)
    
    # --- FIX START: Ensure Session is Created ---
    # We await this here because 'chat' is an async function.
    if session_id not in INITIALIZED_SESSIONS:
        try:
            await runner.session_service.create_session(
                session_id=session_id, 
                user_id="web_user", 
                app_name=APP_NAME
            )
            INITIALIZED_SESSIONS.add(session_id)
        except Exception as e:
            # If session already exists in memory but not in our set, just add it.
            INITIALIZED_SESSIONS.add(session_id)
            print(f"Session init info: {e}")
    # --- FIX END ---
    
    try: content = types.Content(role="user", parts=[types.Part(text=msg)])
    except: content = msg

    final = ""
    try:
        async for event in runner.run_async(user_id="web_user", session_id=session_id, new_message=content):
            try:
                if hasattr(event, 'text') and event.text: final = event.text
                elif hasattr(event, 'content'):
                    for p in event.content.parts:
                        if hasattr(p, 'text'): final += p.text
            except: continue
    except Exception as e: return jsonify({"error": str(e)})
    
    return jsonify({"response": final})

if __name__ == '__main__':
    app.run(debug=True, port=5000)