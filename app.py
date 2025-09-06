import os
import json
import time
import datetime
import random
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- APP & DATABASE CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_changed'
database_url = os.environ.get('DATABASE_URL')
if database_url:
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///fitness_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    workout_logs = db.relationship('WorkoutLog', backref='user', lazy=True, cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    workout_days = db.Column(db.String(100), nullable=False)
    physique_goal = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    equipment = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    workout_name = db.Column(db.String(100))
    plan_details = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    day_of_week = db.Column(db.String(20), nullable=False)
    log_details = db.Column(db.Text, nullable=False)
    todays_weight = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# --- FLASK-LOGIN SETUP ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- KNOWLEDGE BASE WITH WORKING GIFS ---
EXERCISE_KNOWLEDGE_BASE = {
    'cardio': [
        {'name': 'Treadmill', 'gif_url': '/static/assets/treadmill.gif', 'instructions': "<h4>Settings:</h4><ul><li><b>Speed:</b> 5-6 km/h (brisk walk) or 8-10 km/h (light jog).</li><li><b>Incline:</b> 1-2%.</li></ul>"},
        {'name': 'Upright Bike', 'gif_url': '', 'instructions': "<h4>Settings:</h4><ul><li><b>Intensity:</b> Level 8-12.</li></ul>"} # Add GIF URL if you have one
    ],
    'stretches': [
        {'name': 'Quad Stretch', 'gif_url': '', 'instructions': "<p>Hold for 30 seconds per leg.</p>"},
        {'name': 'Hamstring Stretch', 'gif_url': '', 'instructions': "<p>Hold for 30 seconds per leg.</p>"},
        {'name': 'Chest Stretch', 'gif_url': '', 'instructions': "<p>Hold for 30 seconds.</p>"},
        {'name': 'Triceps Stretch', 'gif_url': '', 'instructions': "<p>Hold for 30 seconds per arm.</p>"}
    ],
    'main': {
        'chest': [
            {'name': 'Vertical Chest Press', 'gif_url': '', 'instructions': "<h4>How-To:</h4><p>Sit with your back flat against the pad. Push the handles forward until your arms are fully extended, but don't lock your elbows. Slowly bring the weight back.</p>"},
            {'name': 'Pec Fly Machine', 'gif_url': '', 'instructions': "<h4>How-To:</h4><p>Sit with your back flat against the pad. Bring the handles together in a wide arc, squeezing your chest muscles. Slowly return to the start.</p>"}
        ],
        'back': [
            {'name': 'Lat Pull Down', 'gif_url': '', 'instructions': "<h4>How-To:</h4><p>Grab the bar with a wide, overhand grip. Pull the bar down to your upper chest, squeezing your shoulder blades together. Slowly let the bar return.</p>"},
            {'name': 'Seated Cable Row', 'gif_url': '', 'instructions': "<h4>How-To:</h4><p>Sit with feet braced and back straight. Pull the handle towards your lower abdomen, squeezing your back muscles. Slowly extend your arms back.</p>"}
        ],
        # ... You can find and add other local gif URLs here
    }
}


# --- FINAL AI LOGIC (Shortened for brevity, use your full version) ---
def get_progressive_overload_suggestion(exercise_name, last_log_details, rep_target):
    # This function remains unchanged
    if not last_log_details or exercise_name not in last_log_details: return "<h4>Starting Weight:</h4><p>This is your first time. Find a weight that feels challenging for the target reps (e.g., 15-25 kg).</p>"
    exercise_log = last_log_details.get(exercise_name, {}); last_weight = 0; all_reps_met = True
    logged_sets = [data for set_num, data in exercise_log.items() if set_num.isdigit()]
    if not logged_sets: return "<h4>Starting Weight:</h4><p>Start with a comfortable weight (e.g., 15-25 kg) and focus on form.</p>"
    for set_data in logged_sets:
        reps_done = int(set_data.get('reps', 0)); last_weight = float(set_data.get('weight', 0))
        if reps_done < rep_target: all_reps_met = False; break
    if all_reps_met and last_weight > 0:
        new_weight = last_weight + 2.5
        return f"<h4>This Week's Goal:</h4><p>Last time you lifted {last_weight} kg and hit all your reps. Great work! <b>This week, try for {new_weight} kg.</b></p>"
    elif last_weight > 0: return f"<h4>This Week's Goal:</h4><p>Last time you lifted {last_weight} kg. Focus on hitting all your reps this week with that weight before increasing.</p>"
    return "<h4>Starting Weight:</h4><p>Start with a comfortable weight (e.g., 15-25 kg) and focus on form.</p>"
def generate_ai_workout_plan(user):
    # This function remains unchanged
    profile = user.profile; last_log = WorkoutLog.query.filter_by(user_id=user.id).order_by(WorkoutLog.date.desc()).first()
    last_log_details = json.loads(last_log.log_details) if last_log else {}
    days = profile.workout_days.split(','); goals = profile.physique_goal.split(',')
    if 'bold' in goals or 'strength' in goals: rep_range, rep_target = "4 sets of 6-8 reps", 6
    else: rep_range, rep_target = "3 sets of 10-12 reps", 10
    cardio_duration = 20 if 'stamina' in goals or 'lean' in goals else 10
    split, rotation = {}, []
    if len(days) >= 4: rotation = ['Push', 'Pull', 'Legs']
    elif len(days) == 3: rotation = ['Upper Body', 'Lower Body', 'Full Body']
    else: rotation = ['Full Body']
    if rotation:
        day_map = {name: i for i, name in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
        sorted_days = sorted(days, key=lambda day: day_map.get(day, 7))
        for i, day in enumerate(sorted_days): split[day] = rotation[i % len(rotation)]
    weekly_plan = {}; day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    for day in day_names:
        if day in split:
            workout_type = split[day]; workout = {"workout_name": f"{workout_type} Day", "structure": []}
            workout['structure'].append({"type": "Warm-up", "details": random.choice(EXERCISE_KNOWLEDGE_BASE['cardio']), "duration": "5 minutes"})
            exercises_to_add = []
            # Simplified for brevity - ensure your full exercise selection logic is here
            if 'legs' in EXERCISE_KNOWLEDGE_BASE['main']: exercises_to_add.append(random.choice(EXERCISE_KNOWLEDGE_BASE['main']['legs']))
            if 'back' in EXERCISE_KNOWLEDGE_BASE['main']: exercises_to_add.append(random.choice(EXERCISE_KNOWLEDGE_BASE['main']['back']))
            if 'chest' in EXERCISE_KNOWLEDGE_BASE['main']: exercises_to_add.append(random.choice(EXERCISE_KNOWLEDGE_BASE['main']['chest']))
            for ex_obj in exercises_to_add:
                ex_obj_copy = ex_obj.copy()
                suggestion = get_progressive_overload_suggestion(ex_obj_copy['name'], last_log_details, rep_target)
                ex_obj_copy['instructions'] = suggestion + ex_obj_copy['instructions']
                workout['structure'].append({"type": "Main", "details": ex_obj_copy, "target": rep_range, "rest": "60-90 seconds"})
            workout['structure'].append({"type": "Cardio", "details": random.choice(EXERCISE_KNOWLEDGE_BASE['cardio']), "duration": f"{cardio_duration} minutes"})
            stretches = random.sample(EXERCISE_KNOWLEDGE_BASE['stretches'], 2)
            for stretch_obj in stretches: workout['structure'].append({"type": "Cool-down", "details": stretch_obj, "duration": "30 seconds per side"})
            weekly_plan[day] = workout
        else: weekly_plan[day] = {"workout_name": "Rest Day", "structure": []}
    return weekly_plan

# --- APPLICATION ROUTES (Only workout.html route needs a change) ---
@app.route('/workout/<day>')
@login_required
def workout(day):
    plan = WorkoutPlan.query.filter_by(user_id=current_user.id, day_of_week=day).first()
    if not plan: flash('Workout plan not found.'); return redirect(url_for('dashboard'))
    workout_data = json.loads(plan.plan_details)
    user_profile = current_user.profile
    profile_data = {'weight': user_profile.weight}
    return render_template('workout.html', user=current_user, workout_data=workout_data, profile=profile_data, timestamp=int(time.time()))
@app.route('/')
def index():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return render_template('index.html')
@app.route('/login', methods=['POST'])
def login():
    username, password = request.form.get('username'), request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password): login_user(user); return redirect(url_for('dashboard'))
    flash('Invalid username or password.'); return redirect(url_for('index'))
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        if User.query.filter_by(username=username).first(): flash('Username already exists.'); return redirect(url_for('signup'))
        new_user = User(username=username); new_user.set_password(password)
        db.session.add(new_user); db.session.commit()
        workout_days = request.form.getlist('workout_days')
        physique_goals = request.form.getlist('physique_goal')
        new_profile = UserProfile(age=request.form.get('age'), height=request.form.get('height'), weight=request.form.get('weight'), gender=request.form.get('gender'), workout_days=','.join(workout_days), physique_goal=','.join(physique_goals), duration=float(request.form.get('duration')), equipment=request.form.get('equipment'), user_id=new_user.id)
        db.session.add(new_profile); db.session.commit()
        plan = generate_ai_workout_plan(new_user)
        for day, details in plan.items():
            db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=new_user.id))
        db.session.commit()
        login_user(new_user); return redirect(url_for('dashboard'))
    return render_template('signup.html')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user, timestamp=int(time.time()))
@app.route('/api/save_workout', methods=['POST'])
@login_required
def save_workout():
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    new_log = WorkoutLog(day_of_week=data.get('dayOfWeek'), log_details=json.dumps(data.get('logDetails')), todays_weight=data.get('todaysWeight') if data.get('todaysWeight') else None, user_id=current_user.id)
    db.session.add(new_log); db.session.commit()
    WorkoutPlan.query.filter_by(user_id=current_user.id).delete()
    new_plan = generate_ai_workout_plan(current_user)
    for day, details in new_plan.items():
        db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=current_user.id))
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Workout saved'})
@app.route('/api/get_plan')
@login_required
def get_plan():
    user_plans = WorkoutPlan.query.filter_by(user_id=current_user.id).all()
    if not user_plans:
        new_plan = generate_ai_workout_plan(current_user)
        for day, details in new_plan.items():
            db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=current_user.id))
        db.session.commit()
        user_plans = WorkoutPlan.query.filter_by(user_id=current_user.id).all()
    plan_data = {}
    for plan in user_plans:
        details = json.loads(plan.plan_details)
        structure = details.get('structure', [])
        if structure: exercise_names = [item.get('details', {}).get('name', 'Unnamed Step') for item in structure]
        else: exercise_names = []
        plan_data[plan.day_of_week] = {"workout_name": plan.workout_name, "exercises": exercise_names}
    return jsonify(plan_data)
@app.route('/performance')
@login_required
def performance():
    return render_template('performance.html', user=current_user, timestamp=int(time.time()))
@app.route('/api/get_performance_data')
@login_required
def get_performance_data():
    logs = WorkoutLog.query.filter_by(user_id=current_user.id).order_by(WorkoutLog.date.asc()).all()
    weight_labels = [log.date.strftime('%b %d') for log in logs if log.todays_weight]
    weight_data = [log.todays_weight for log in logs if log.todays_weight]
    volume_labels, volume_data = [], []
    exercise_progression = {}
    for log in logs:
        volume_labels.append(log.date.strftime('%b %d') + f" ({log.day_of_week[:3]})")
        total_volume = 0
        log_details = json.loads(log.log_details)
        for exercise, sets in log_details.items():
            max_e1rm = 0
            if not exercise_progression.get(exercise): exercise_progression[exercise] = {'labels': [], 'data': []}
            for set_num, data in sets.items():
                if set_num.isdigit():
                    try:
                        weight, reps = float(data.get('weight', 0)), int(data.get('reps', 0))
                        if weight > 0 and reps > 0:
                            total_volume += weight * reps
                            e1rm = weight / (1.0278 - (0.0278 * reps))
                            if e1rm > max_e1rm: max_e1rm = e1rm
                    except (ValueError, TypeError): continue
            if max_e1rm > 0:
                exercise_progression[exercise]['labels'].append(log.date.strftime('%b %d'))
                exercise_progression[exercise]['data'].append(round(max_e1rm, 1))
        volume_data.append(total_volume)
    return jsonify({'weight_logs': {'labels': weight_labels, 'data': weight_data}, 'volume_logs': {'labels': volume_labels, 'data': volume_data}, 'exercise_progression': exercise_progression})
@app.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)
