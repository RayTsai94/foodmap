#!/bin/bash

# Install dependencies
pip install -r requirements_vercel.txt

# Collect static files
python manage.py collectstatic --noinput --clear 