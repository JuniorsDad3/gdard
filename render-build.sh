#!/usr/bin/env bash

# Install ODBC Driver 18 for SQL Server
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list)"
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev odbcinst msodbcsql18

# Start the app
gunicorn run:app
