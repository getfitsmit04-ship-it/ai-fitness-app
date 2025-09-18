# inspect_profile.py
from app import db, User, UserProfile

# Open an app context to use SQLAlchemy properly
with db.app.app_context():
    users = User.query.all()
    print(f"Total users: {len(users)}")
    for u in users:
        print("----")
        print(f"User ID: {u.id}, username: {u.username}")
        if u.profile:
            print("  Age:", u.profile.age)
            print("  Height:", u.profile.height)
            print("  Weight:", u.profile.weight)
            print("  Gender:", u.profile.gender)
            print("  Workout Days (raw stored CSV):", u.profile.workout_days)
            print("  Goals:", u.profile.physique_goal)
            print("  Duration:", u.profile.duration)
            print("  Equipment:", u.profile.equipment)
            print("  Focus Areas:", u.profile.focus_areas)
        else:
            print("  No profile setup yet")
