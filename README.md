🏆 Pokémon Showdown Competitive Coach

Victory Road AI is an intelligent agent designed to bridge the massive skill gap between casual play and the competitive ladder. With the upcoming mobile release of Pokémon Champions, millions of new players will face a steep learning curve. This tool serves as their dedicated, always-available mentor.

🚀 The Problem

Transitioning from single-player to competitive Pokémon is like jumping from Checkers to Chess. New players face three major barriers:

The Knowledge Cliff: Simple strategies fail against human prediction.

Meta Velocity: The competitive landscape shifts daily, making static guides obsolete.

Analysis Paralysis: Overwhelmed by 1,000+ characters and billions of combinations.

💡 The Solution

Unlike standard chatbots that hallucinate outdated strategies, this Agent uses Google Gemini and the Google Agent Development Kit (ADK) to:

Actively Research: Queries live usage stats APIs to find what strategies are working right now.

Contextualize: Adapts advice based on whether you are a Beginner or Expert.

Validate: Ensures every team is 100% legal and ready for import into Pokémon Showdown.

🛠️ Tech Stack

Brain: Google Gemini 2.5 Pro

Orchestration: Google Agent Development Kit (ADK)

Backend: Python & Flask

Database: MongoDB

Data Source: External Competitive APIs (pkmn.cc)

⚡ Key Features

Real-Time Meta Analysis: Fetches current pick rates and counters.

Team Export: Generates Showdown-importable text blocks instantly.

Stateful Coaching: Remembers your team context for iterative improvements.

Profile System: Save and manage your favorite teams.

📦 Installation

Clone the repo:

git clone [https://github.com/yourusername/showdown-comp-coach.git](https://github.com/yourusername/showdown-comp-coach.git)
cd showdown-comp-coach


Install dependencies:

pip install -r requirements.txt


Set up environment variables:
Create a .env file and add your keys:

GOOGLE_API_KEY=your_key_here
MONGODB_URI=your_mongo_uri
SECRET_KEY=your_secret_key


Run the App:

python app.py
