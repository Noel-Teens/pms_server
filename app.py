import os

# ---- STEP 2: Create db.sqlite3 if missing (to avoid SQLite open errors)
db_path = os.path.join(os.getcwd(), "db.sqlite3")
if not os.path.exists(db_path):
    with open(db_path, 'w') as f:
        f.write("")  # just create an empty file

# ---- STEP 3: Run migrations to initialize database
os.system("python manage.py makemigrations")
os.system("python manage.py migrate")
os.system("python manage.py createsuperadmin --username=Admin --email=admin@gmail.com --password=adminpassword")


# ---- STEP 4: Start Django dev server on required Hugging Face port
os.system("uvicorn pms_server.asgi:application --host 0.0.0.0 --port 7860")