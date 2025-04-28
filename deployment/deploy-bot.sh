#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "MONGODB_URI=your_mongodb_connection_string_here" > .env
    echo "Please update the .env file with your MongoDB connection string!"
fi

# Set up as a service with systemd if on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Setting up systemd service..."
    BOT_DIR=$(pwd)
    
    # Create systemd service file
    cat > linkedin-bot.service <<EOL
[Unit]
Description=LinkedIn Bot Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=${BOT_DIR}
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/bot-server.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=linkedin-bot

[Install]
WantedBy=multi-user.target
EOL

    # Install the service
    sudo mv linkedin-bot.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable linkedin-bot
    sudo systemctl start linkedin-bot
    
    echo "Bot service installed and started!"
    echo "Check status with: sudo systemctl status linkedin-bot"
else
    # For non-Linux systems, provide instructions to run manually
    echo "To start the bot server, run:"
    echo "source venv/bin/activate && python bot-server.py"
fi

echo "Bot deployment complete!"