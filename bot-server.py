#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import threading
import json
import os
import logging
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot-server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB Configuration
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    logger.error("MongoDB URI not found in environment variables!")
    MONGO_URI = "mongodb://localhost:27017/"

client = MongoClient(MONGO_URI)
db = client.get_database("linkedin_bot_db")
bot_runs_collection = db.bot_usage

def run_bot(user_email, user_name):
    """Run the bot in a separate thread."""
    try:
        logger.info(f"Starting bot for user: {user_email}")
        
        # Record bot run start in database
        run_id = bot_runs_collection.insert_one({
            "email": user_email,
            "name": user_name,
            "action": "bot_run",
            "status": "running",
            "timestamp": datetime.datetime.utcnow()
        }).inserted_id
        
        # Run the bot script with the user's email
        result = subprocess.run(
            ["python", "linkedin_bot.py", "--email", user_email, "--name", user_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log the output
        logger.info(f"Bot completed for {user_email}. Output: {result.stdout}")
        
        # Update the record in the database
        bot_runs_collection.update_one(
            {"_id": run_id},
            {"$set": {
                "status": "completed",
                "completedAt": datetime.datetime.utcnow(),
                "output": result.stdout,
                "success": True
            }}
        )
        
        return True
    except subprocess.CalledProcessError as e:
        # Log the error
        logger.error(f"Bot failed for {user_email}. Error: {e.stderr}")
        
        # Update the record in the database
        if 'run_id' in locals():
            bot_runs_collection.update_one(
                {"_id": run_id},
                {"$set": {
                    "status": "failed",
                    "completedAt": datetime.datetime.utcnow(),
                    "error": e.stderr,
                    "success": False
                }}
            )
        
        return False
    except Exception as e:
        logger.exception(f"Unexpected error running bot for {user_email}: {str(e)}")
        
        # Update the record in the database
        if 'run_id' in locals():
            bot_runs_collection.update_one(
                {"_id": run_id},
                {"$set": {
                    "status": "error",
                    "completedAt": datetime.datetime.utcnow(),
                    "error": str(e),
                    "success": False
                }}
            )
        
        return False

@app.route('/run-bot', methods=['POST'])
def trigger_bot():
    """API endpoint to trigger the bot."""
    try:
        data = request.json
        
        if not data or 'userEmail' not in data:
            return jsonify({"error": "Missing required user email"}), 400
        
        user_email = data.get('userEmail')
        user_name = data.get('userName', 'User')
        
        # Log the bot trigger in MongoDB
        db.bot_usage.insert_one({
            "email": user_email,
            "name": user_name,
            "action": "bot_triggered",
            "timestamp": datetime.datetime.utcnow()
        })
        
        # Start the bot in a separate thread
        thread = threading.Thread(target=run_bot, args=(user_email, user_name))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Bot started for {user_email}",
        })
    except Exception as e:
        logger.exception(f"Error in /run-bot endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Simple status endpoint to check if the service is running."""
    return jsonify({"status": "online"})

if __name__ == '__main__':
    # Log startup
    logger.info("Bot server starting up...")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)