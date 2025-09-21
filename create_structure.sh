#!/bin/bash

# Create main project directory
mkdir -p gdard-smart-ag
cd gdard-smart-ag || exit

# Create core app structure
mkdir -p \
  app/auth \
  app/farmer \
  app/admin \
  app/api \
  app/static/css \
  app/static/js \
  app/static/images \
  app/static/data \
  app/templates/auth \
  app/templates/farmer \
  app/templates/admin \
  app/templates/shared \
  migrations \
  instance \
  tests \
  venv

# Create root-level files
touch \
  requirements.txt \
  config.py \
  excel_handler.py \
  iot_integration.py \
  drone_analysis.py \
  predictive_analytics.py \
  email_service.py

# Create app-level files
touch app/__init__.py
touch app/models.py

# Auth blueprint files
touch app/auth/__init__.py
touch app/auth/routes.py
touch app/auth/forms.py

# Farmer blueprint files
touch app/farmer/__init__.py
touch app/farmer/routes.py
touch app/farmer/utils.py

# Admin blueprint files
touch app/admin/__init__.py
touch app/admin/routes.py

# API files
touch app/api/__init__.py
touch app/api/iot.py
touch app/api/weather.py

# Template base
touch app/templates/base.html

# Instance config
touch instance/config.py

echo "Project structure for gdard-smart-ag created successfully."
