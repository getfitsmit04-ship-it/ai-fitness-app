# --- IMPORTS ---
import os
import json
import time
import random
import datetime
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- APP & DATABASE CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_local_dev')
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///fitness_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

# --- DATABASE MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    workout_logs = db.relationship('WorkoutLog', backref='user', lazy=True, cascade="all, delete-orphan")
    previous_logs = db.relationship('PreviousLog', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    focus_areas = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PreviousLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    kg = db.Column(db.Float, nullable=True)
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

# --- EXERCISE KNOWLEDGE BASE (EXPLAIN LIKE YOU'RE 5) ---
EXERCISE_KNOWLEDGE_BASE = {
    'warmup_dynamic': [
        {'name': 'Arm Circles', 'instructions': "Spin your arms in little circles like an airplane. 20 seconds forward, 20 backward."},
        {'name': 'Torso Twists', 'instructions': "Twist your body gently left and right. Pretend you're looking behind you. 30 seconds."},
        {'name': 'Shoulder Rolls', 'instructions': "Lift your shoulders up and back, like shrugging but slow. 20 seconds."},
        {'name': 'Leg Swings', 'instructions': "Swing one leg forward and back like a pendulum. Then the other leg. 15 times each."}
    ],
    'cardio': [
        {'name': 'Treadmill', 'instructions': "Walk or jog. Keep your feet moving fast. Speed 5-6 for walking, 8-10 for jogging. Incline 1-2%."},
        {'name': 'Elliptical', 'instructions': "Move your legs and arms like skating. Keep it steady, not too fast."}
    ],
    'main': {
        'chest': [
            {'name': 'Incline Chest Press', 'instructions': "Push the handles up slowly. Pretend you're pushing a big box up. Squeeze your chest at the top."},
            {'name': 'Vertical Chest Press', 'instructions': "Push straight out. Keep your back flat. Don't lock elbows."},
            {'name': 'Pec Fly', 'instructions': "Open your arms wide like hugging a big tree. Squeeze your chest when closing arms."}
        ],
        'back': [
            {'name': 'Lat Pull Down', 'instructions': "Pull the bar down to your chest like you're bringing a rope to you. Keep your tummy tight."},
            {'name': 'Long Pull Row', 'instructions': "Pull handles to your tummy like you're rowing a boat. Keep back straight."}
        ],
        'shoulders': [
            {'name': 'Lateral Raise Machine', 'instructions': "Lift your arms sideways to shoulder height. Don't shrug."},
            {'name': 'Overhead Press Machine', 'instructions': "Push handles up over your head. Keep back straight."}
        ],
        'biceps': [
            {'name': 'Bicep Curls Machine', 'instructions': "Curl your arms like lifting a small bucket. Keep elbows still."}
        ],
        'triceps': [
            {'name': 'Seated Tricep Machine', 'instructions': "Push down slowly. Feel the back of your arms working."}
        ],
        'quads': [
            {'name': 'Leg Extension', 'instructions': "Push legs straight. Pretend kicking a ball gently."}
        ],
        'hamstrings': [
            {'name': 'Seated Leg Curls', 'instructions': "Pull heels back like trying to touch your bottom. Go slow."}
        ],
        'calves': [
            {'name': 'Standing Calf Raise', 'instructions': "Stand on tiptoes like a ballerina. Go up and down slowly."}
        ],
        'core': [
            {'name': 'Abdominal Machine', 'instructions': "Push tummy towards knees. Don't use arms, just tummy muscles."}
        ]
    },
    'cooldown_static': [
        {'name': 'Quad Stretch', 'instructions': "Hold one leg behind you like a ballerina. Count 30 slowly."},
        {'name': 'Hamstring Stretch', 'instructions': "Reach for your toes gently. Count 30 slowly."},
        {'name': 'Chest Stretch', 'instructions': "Open arms wide and feel chest stretch. Count 30."},
        {'name': 'Triceps Stretch', 'instructions': "Lift one arm up and bend behind head. Use other hand gently. Count 30."}
    ]
}

@app.context_processor
def inject_exercise_library():
    flat_library = []
    for cat in EXERCISE_KNOWLEDGE_BASE['main'].values():
        flat_library.extend(cat)
    return dict(EXERCISE_LIBRARY=list({v['name']: v for v in flat_library}.values()))

# --- PROGRESSIVE OVERLOAD LOGIC ---
def get_progressive_overload_suggestion(exercise_name, last_log_details, rep_target):
    if not last_log_details or exercise_name not in last_log_details:
        return "<p>This is your first time doing this exercise. Pick a weight that is challenging but safe.</p>"

    exercise_log = last_log_details.get(exercise_name, {})
    last_weight = 0
    all_reps_met = True
    logged_sets = [data for set_num, data in exercise_log.items() if set_num.isdigit()]
    if not logged_sets:
        return "<p>Start light and focus on form!</p>"

    for set_data in logged_sets:
        reps_done = int(set_data.get('reps', 0))
        last_weight = float(set_data.get('weight', 0))
        if reps_done < rep_target:
            all_reps_met = False
            break

    if all_reps_met and last_weight > 0:
        new_weight = last_weight + 2.5
        return f"<p>Last time you lifted {last_weight}kg and did all reps. Awesome! Try {new_weight}kg this time.</p>"
    elif last_weight > 0:
        return f"<p>Last time you lifted {last_weight}kg. Focus on doing all reps first before increasing weight.</p>"
    return "<p>Start light and focus on form!</p>"

# --- AI WORKOUT PLAN GENERATION ---
def generate_ai_workout_plan(user):
    profile = user.profile
    last_log = WorkoutLog.query.filter_by(user_id=user.id).order_by(WorkoutLog.date.desc()).first()
    last_log_details = json.loads(last_log.log_details) if last_log else {}
    previous_exercises = [log.exercise_name for log in user.previous_logs]
    focus_areas = profile.focus_areas.split(',') if profile.focus_areas else []
    days = profile.workout_days.split(',')
    goals = profile.physique_goal.split(',')

    rep_range, rep_target = ("4 sets of 6-8 reps", 6) if 'bold' in goals or 'strength' in goals else ("3 sets of 10-12 reps", 10)
    cardio_duration = 20 if 'stamina' in goals or 'lean' in goals else 10
    rotation = ['Push', 'Pull', 'Legs'] if len(days) >= 4 else ['Upper Body', 'Lower Body', 'Full Body'] if len(days) == 3 else ['Full Body']
    split = {}
    day_map = {name: i for i, name in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
    sorted_days = sorted(days, key=lambda day: day_map.get(day, 7))
    for i, day in enumerate(sorted_days):
        split[day] = rotation[i % len(rotation)]

    weekly_plan = {}
    for day_name in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
        if day_name in split:
            workout_type = split[day_name]
            workout = {"workout_name": f"{workout_type} Day", "structure": []}

            # Warm-up
            workout['structure'].append({"type": "Warm-up", "details": EXERCISE_KNOWLEDGE_BASE['cardio'][0], "duration": "5 min"})
            workout['structure'].extend([{"type": "Warm-up", "details": ex, "duration": "30 sec"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['warmup_dynamic'], 2)])

            # Main exercises
            exercises_to_add = []
            def get_available_exercises(muscle):
                return [ex for ex in EXERCISE_KNOWLEDGE_BASE['main'].get(muscle, []) if ex['name'] not in previous_exercises] or EXERCISE_KNOWLEDGE_BASE['main'].get(muscle, [])

            if workout_type == 'Push':
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), 2) + random.sample(get_available_exercises('triceps'), 1))
            elif workout_type == 'Pull':
                exercises_to_add.extend(random.sample(get_available_exercises('back'), 2) + random.sample(get_available_exercises('biceps'), 1))
            elif workout_type in ['Legs', 'Lower Body']:
                exercises_to_add.extend(random.sample(get_available_exercises('quads'), 1) + random.sample(get_available_exercises('hamstrings'), 1) + random.sample(get_available_exercises('calves'), 1))
            else:
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), 1) + random.sample(get_available_exercises('back'), 1) + random.sample(get_available_exercises('quads'), 1))

            for area in focus_areas:
                if area in EXERCISE_KNOWLEDGE_BASE['main']:
                    exercises_to_add.append(random.choice(get_available_exercises(area)))

            unique_exercises = list({ex['name']: ex for ex in exercises_to_add}.values())
            for ex_obj in unique_exercises:
                ex_copy = ex_obj.copy()
                suggestion = get_progressive_overload_suggestion(ex_copy['name'], last_log_details, rep_target)
                ex_copy['instructions'] = suggestion + "<br>" + ex_copy.get('instructions', '')
                workout['structure'].append({"type": "Main", "details": ex_copy, "target": rep_range, "rest": "60-90 sec"})

            # Cooldown
            workout['structure'].append({"type": "Cooldown Cardio", "details": EXERCISE_KNOWLEDGE_BASE['cardio'][1], "duration": "5-10 min"})
            workout['structure'].extend([{"type": "Stretching", "details": ex, "duration": "30 sec"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['cooldown_static'], 2)])

            weekly_plan[day_name] = workout
        else:
            weekly_plan[day_name] = None

    return weekly_plan

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', timestamp=int(time.time()))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('signup'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('profile_setup'))
    return render_template('signup.html', timestamp=int(time.time()))

@app.route('/profile_setup', methods=['GET','POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        profile = UserProfile(
            age=int(request.form.get('age')),
            height=int(request.form.get('height')),
            weight=float(request.form.get('weight')),
            gender=request.form.get('gender'),
            workout_days=','.join(request.form.getlist('workout_days')),
            physique_goal=','.join(request.form.getlist('physique_goal')),
            duration=float(request.form.get('duration')),
            equipment=','.join(request.form.getlist('equipment')),
            focus_areas=','.join(request.form.getlist('focus_areas')),
            user_id=current_user.id
        )
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('profile_setup.html', timestamp=int(time.time()))

@app.route('/dashboard')
@login_required
def dashboard():
    plan = generate_ai_workout_plan(current_user)
    return render_template('dashboard.html', plan=plan, timestamp=int(time.time()))

@app.route('/performance')
@login_required
def performance():
    return render_template('performance.html', timestamp=int(time.time()))

@app.route('/api/get_performance_data')
@login_required
def get_performance_data():
    weight_logs = WorkoutLog.query.filter_by(user_id=current_user.id).order_by(WorkoutLog.date).all()
    weight_labels, weight_data = [], []
    volume_labels, volume_data = [], []
    exercise_progression = {}

    for log in weight_logs:
        weight_labels.append(log.date.strftime("%d-%b"))
        weight_data.append(log.todays_weight or 0)

        log_details = json.loads(log.log_details)
        total_volume = 0
        for ex_name, sets_dict in log_details.items():
            exercise_progression.setdefault(ex_name, {'labels': [], 'data': []})
            max_weight = max([float(s['weight']) for k,s in sets_dict.items() if k.isdigit()] or [0])
            exercise_progression[ex_name]['labels'].append(log.date.strftime("%d-%b"))
            exercise_progression[ex_name]['data'].append(max_weight)

            for set_data in sets_dict.values():
                total_volume += int(set_data.get('reps', 0)) * float(set_data.get('weight', 0))
        volume_labels.append(log.date.strftime("%d-%b"))
        volume_data.append(total_volume)

    return jsonify({
        'weight_logs': {'labels': weight_labels, 'data': weight_data},
        'volume_logs': {'labels': volume_labels, 'data': volume_data},
        'exercise_progression': exercise_progression
    })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
