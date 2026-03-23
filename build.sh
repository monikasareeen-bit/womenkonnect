#!/bin/bash
pip install -r requirements.txt
python manage.py migrate
python promote_admin.py   # no passwords here