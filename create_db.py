from app import app, db

# This script creates the database tables based on your models.
# It's run once during the initial build on Render.
with app.app_context():
    db.create_all()

print("Database tables created successfully.")