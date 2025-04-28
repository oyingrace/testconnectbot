#!/usr/bin/env python3
import os
import time
import json
import argparse
import sys
from colorama import Fore, Style, init
from pymongo import MongoClient
import datetime

# Initialize colorama
init()

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_to_mongodb():
    """Connect to MongoDB."""
    try:
        # Read MongoDB connection string from environment
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            # Try to read from config file
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    mongo_uri = config.get("mongo_uri")
        
        if not mongo_uri:
            print(f"{Fore.RED}Error: MongoDB connection string not found!{Style.RESET_ALL}")
            print("Please set MONGODB_URI environment variable or add it to config.json")
            return None
            
        client = MongoClient(mongo_uri)
        # Ping the database to check connection
        client.admin.command('ping')
        
        return client
    except Exception as e:
        print(f"{Fore.RED}Error connecting to MongoDB: {str(e)}{Style.RESET_ALL}")
        return None

def display_welcome_header():
    """Display a styled header."""
    print("┌" + "─" * 50 + "┐")
    print("│" + f"{Fore.BLUE} LinkedIn Auto-Apply Bot {Style.RESET_ALL}".center(50) + "│")
    print("└" + "─" * 50 + "┘")

def display_user_info(name, email):
    """Display user information in a styled box."""
    print("┌" + "─" * 50 + "┐")
    print("│" + " User Information ".center(50) + "│")
    print("├" + "─" * 50 + "┤")
    
    # Display name
    print("│" + f" Name: {Fore.GREEN}{name}{Style.RESET_ALL}".ljust(50) + "│")
    
    # Display email
    print("│" + f" Email: {Fore.CYAN}{email}{Style.RESET_ALL}".ljust(50) + "│")
    
    # Display current time
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("│" + f" Run Time: {current_time}".ljust(50) + "│")
    print("└" + "─" * 50 + "┘")

def main():
    """Main function to run the bot."""
    parser = argparse.ArgumentParser(description='LinkedIn Auto-Apply Bot')
    parser.add_argument('--email', required=True, help='User email')
    parser.add_argument('--name', default='User', help='User name')
    parser.add_argument('--no-clear', action='store_true', help='Do not clear the screen')
    args = parser.parse_args()
    
    if not args.no_clear:
        clear_screen()
    
    # Display welcome message
    display_welcome_header()
    
    # Display user info from arguments
    display_user_info(args.name, args.email)
    
    # Connect to MongoDB
    mongo_client = connect_to_mongodb()
    if mongo_client:
        print(f"\n{Fore.GREEN}Successfully connected to MongoDB{Style.RESET_ALL}")
        
        # Access the user database
        db = mongo_client.get_database("linkedin_bot_db")
        
        # Log this run
        db.bot_usage.insert_one({
            "email": args.email,
            "name": args.name,
            "action": "bot_run",
            "timestamp": datetime.datetime.utcnow()
        })
        
        print(f"\n{Fore.YELLOW}Bot execution logged to database{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}Warning: Not connected to MongoDB, running in offline mode{Style.RESET_ALL}")
    
    # Simulate bot activity
    print(f"\n{Fore.CYAN}Starting LinkedIn auto-apply process for {args.email}...{Style.RESET_ALL}")
    
    # Here you would implement your actual LinkedIn automation
    for i in range(5):
        print(f"Processing step {i+1} of 5...")
        time.sleep(1)
    
    print(f"\n{Fore.GREEN}Bot execution completed successfully!{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting LinkedIn Auto-Apply Bot...")
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)