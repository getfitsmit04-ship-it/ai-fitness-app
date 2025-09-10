# --- IMPORTS ---
import os
import json
import time
import datetime
import random
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

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
    password_hash = db.Column(db.String(225), nullable=False)
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    workout_logs = db.relationship('WorkoutLog', backref='user', lazy=True, cascade="all, delete-orphan")
    previous_logs = db.relationship('PreviousLog', backref='user', lazy=True, cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True); age = db.Column(db.Integer, nullable=False); height = db.Column(db.Integer, nullable=False); weight = db.Column(db.Float, nullable=False); gender = db.Column(db.String(50), nullable=False); workout_days = db.Column(db.String(100), nullable=False); physique_goal = db.Column(db.String(200), nullable=False); duration = db.Column(db.Float, nullable=False); equipment = db.Column(db.String(100), nullable=False); focus_areas = db.Column(db.String(200), nullable=True); user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PreviousLog(db.Model):
    id = db.Column(db.Integer, primary_key=True); exercise_name = db.Column(db.String(100), nullable=False); sets = db.Column(db.Integer, nullable=True); reps = db.Column(db.Integer, nullable=True); kg = db.Column(db.Float, nullable=True); user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WorkoutPlan(db.Model): id = db.Column(db.Integer, primary_key=True); day_of_week = db.Column(db.String(20), nullable=False); workout_name = db.Column(db.String(100)); plan_details = db.Column(db.Text, nullable=False); user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WorkoutLog(db.Model): id = db.Column(db.Integer, primary_key=True); date = db.Column(db.Date, nullable=False, default=datetime.date.today); day_of_week = db.Column(db.String(20), nullable=False); log_details = db.Column(db.Text, nullable=False); todays_weight = db.Column(db.Float); user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# --- FLASK-LOGIN SETUP ---
@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))


# --- DEFINITIVE, COMPREHENSIVE EXERCISE KNOWLEDGE BASE ---
EXERCISE_KNOWLEDGE_BASE = {
    'warmup_dynamic': [
        {'name': 'Arm Circles'}, {'name': 'Torso Twists'}, {'name': 'Shoulder Rolls'}, {'name': 'Leg Swings'}
    ],
    'cardio': [
        {'name': 'Treadmill'}, {'name': 'Elliptical'}, {'name': 'Upright Bike'}, {'name': 'Recumbent Bike'}, {'name': 'Rowing Machine'}, {'name': 'Stair Master'}
    ],
    'main': {
        'chest': [{'name': 'Incline Chest Press'}, {'name': 'Vertical Chest Press'}, {'name': 'Pec Fly'}],
        'back': [{'name': 'Lat Pull Down'}, {'name': 'Long Pull Row'}, {'name': 'Assisted Chin-ups'}, {'name': 'Pull Down'}, {'name': 'Linear Row'}],
        'shoulders': [{'name': 'Lateral Raise Machine'}, {'name': 'Overhead Press Machine'}],
        'biceps': [{'name': 'Bicep Curls Machine'}],
        'triceps': [{'name': 'Seated Tricep Machine'}, {'name': 'Assisted Dips'}, {'name': 'Seated Triba Trainer'}],
        'quads': [{'name': 'Leg Extension'}, {'name': 'Power Squad Machine'}],
        'hamstrings': [{'name': 'Seated Leg Curls'}, {'name': 'Kneeling Leg Curl'}, {'name': 'Isolateral Leg Curls'}],
        'calves': [{'name': 'Standing Calf Raise'}, {'name': 'Seated Calf Raise'}],
        'hips': [{'name': 'Hip Abductor Machine'}, {'name': 'Hip Adductor Machine'}],
        'core': [{'name': 'Abdominal Machine'}, {'name': 'Torso Rotation Machine'}],
        'forearms': [{'name': 'Wrist Curls'}],
        'full_body_versatile': [
            {'name': 'Smith Machine Squats'}, {'name': 'Smith Machine Bench Press'},
            {'name': 'Dumbbell Bench Press'}, {'name': 'Dumbbell Rows'}, {'name': 'Dumbbell Shoulder Press'},
            {'name': 'Kettlebell Swings'}, {'name': 'Kettlebell Goblet Squats'},
            {'name': 'Cable Wood Chops'}, {'name': 'Cable Pallof Press'},
            {'name': 'Resistance Band Pull-Aparts'}, {'name': 'Banded Glute Bridges'}
        ]
    },
    'cooldown_static': [
        {'name': 'Quad Stretch'}, {'name': 'Hamstring Stretch'}, {'name': 'Chest Stretch'}, {'name': 'Triceps Stretch'}, {'name': 'Glute Stretch (Pigeon Pose)'}
    ]
}

@app.context_processor
def inject_exercise_library():
    flat_library = []
    for category in EXERCISE_KNOWLEDGE_BASE['main'].values():
        flat_library.extend(category)
    unique_library = list({v['name']: v for v in flat_library}.values())
    return dict(EXERCISE_LIBRARY=unique_library)

# --- FINAL AI LOGIC ---
def generate_ai_workout_plan(user):
    profile = user.profile
    last_log = WorkoutLog.query.filter_by(user_id=user.id).order_by(WorkoutLog.date.desc()).first()
    last_log_details = json.loads(last_log.log_details) if last_log else {}
    previous_exercises = [log.exercise_name for log in user.previous_logs]
    focus_areas = profile.focus_areas.split(',') if profile.focus_areas else []
    days = profile.workout_days.split(',')
    goals = profile.physique_goal.split(',')
    
    rep_range, _ = ("4 sets of 6-8 reps", 6) if 'bold' in goals or 'strength' in goals else ("3 sets of 10-12 reps", 10)
    cardio_duration = 20 if 'stamina' in goals or 'lean' in goals else 10
    
    rotation = ['Push', 'Pull', 'Legs'] if len(days) >= 4 else ['Upper Body', 'Lower Body', 'Full Body'] if len(days) == 3 else ['Full Body']
    split = {}
    if rotation:
        day_map = {name: i for i, name in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
        sorted_days = sorted(days, key=lambda day: day_map.get(day, 7))
        for i, day in enumerate(sorted_days):
            split[day] = rotation[i % len(rotation)]

    weekly_plan = {}
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    for day in day_names:
        if day in split:
            workout_type = split[day]
            workout = {"workout_name": f"{workout_type} Day", "structure": []}
            
            # 1. Warm-up
            workout['structure'].append({"type": "Warm-up", "details": {"name": "Treadmill (Warmup)"}, "duration": "5 minutes"})
            workout['structure'].extend([{"type": "Warm-up", "details": ex, "duration": "30 seconds"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['warmup_dynamic'], 2)])

            # 2. Main Exercises
            exercises_to_add = []
            def get_available_exercises(group):
                return [ex for ex in EXERCISE_KNOWLEDGE_BASE['main'].get(group, []) if ex['name'] not in previous_exercises] or EXERCISE_KNOWLEDGE_BASE['main'].get(group, [])

            if workout_type == 'Push':
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), 2) + random.sample(get_available_exercises('triceps'), 1))
            elif workout_type == 'Pull':
                exercises_to_add.extend(random.sample(get_available_exercises('back'), 2) + random.sample(get_available_exercises('biceps'), 1))
            elif workout_type in ['Legs', 'Lower Body']:
                exercises_to_add.extend(random.sample(get_available_exercises('quads'), 1) + random.sample(get_available_exercises('hamstrings'), 1) + random.sample(get_available_exercises('calves'), 1))
            else: # Full Body or Upper Body
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), 1) + random.sample(get_available_exercises('back'), 1) + random.sample(get_available_exercises('quads'), 1))

            # 3. Focus Area Exercises
            for area in focus_areas:
                if area in EXERCISE_KNOWLEDGE_BASE['main']:
                    exercises_to_add.append(random.choice(get_available_exercises(area)))
            
            unique_exercises = list({ex['name']: ex for ex in exercises_to_add}.values())

            for ex_obj in unique_exercises:
                ex_obj_copy = ex_obj.copy()
                suggestion = "<h4>Starting Weight:</h4><p>e.g. 15-25 kg</p>" # Simplified
                ex_obj_copy['instructions'] = suggestion + ex_obj_copy.get('instructions', '')
                workout['structure'].append({"type": "Main", "details": ex_obj_copy, "target": rep_range, "rest": "60-90 seconds"})
            
            # 4. Cooldown Cardio
            workout['structure'].append({"type": "Cooldown Cardio", "details": {"name": "Elliptical (Cooldown)"}, "duration": "5-10 minutes"})

            # 5. Stretching
            workout['structure'].extend([{"type": "Stretching", "details": ex, "duration": "30 seconds"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['cooldown_static'], 2)])

            weekly_plan[day] = workout
        else:
            weekly_plan[day] = {"workout_name": "Rest Day", "structure": []}
            
    return weekly_plan

# --- APPLICATION ROUTES ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        new_user = User(username=request.form.get('username'))
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        
        new_profile = UserProfile(
            age=request.form.get('age'), height=request.form.get('height'), weight=request.form.get('weight'), gender=request.form.get('gender'), 
            workout_days=','.join(request.form.getlist('workout_days')), 
            physique_goal=','.join(request.form.getlist('physique_goal')), 
            duration=float(request.form.get('duration')), 
            equipment=request.form.get('equipment'), 
            focus_areas=','.join(request.form.getlist('focus_areas')), 
            user_id=new_user.id
        )
        db.session.add(new_profile)
        
        prev_exercises = request.form.getlist('prev_exercise')
        for ex_name in prev_exercises:
            sets = request.form.get(f"prev_{ex_name}_sets")
            reps = request.form.get(f"prev_{ex_name}_reps")
            kg = request.form.get(f"prev_{ex_name}_kg")
            
            db.session.add(PreviousLog(
                exercise_name=ex_name,
                sets=int(sets) if sets else None,
                reps=int(reps) if reps else None,
                kg=float(kg) if kg else None,
                user_id=new_user.id
            ))
        
        db.session.commit()
        
        plan = generate_ai_workout_plan(new_user)
        for day, details in plan.items():
            db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=new_user.id))
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime('%A')
    
    workout_days = current_user.profile.workout_days.split(',')
    missed_workout = None
    if yesterday_str in workout_days:
        log_for_yesterday = WorkoutLog.query.filter_by(user_id=current_user.id, date=yesterday).first()
        if not log_for_yesterday:
            missed_plan = WorkoutPlan.query.filter_by(user_id=current_user.id, day_of_week=yesterday_str).first()
            if missed_plan:
                missed_workout = { "day": yesterday_str, "name": missed_plan.workout_name }
                
    return render_template('dashboard.html', user=current_user, timestamp=int(time.time()), missed_workout=missed_workout)

@app.route('/workout/<day>')
@login_required
def workout(day):
    plan = WorkoutPlan.query.filter_by(user_id=current_user.id, day_of_week=day).first()
    if not plan:
        flash('Workout plan not found.')
        return redirect(url_for('dashboard'))
    workout_data = json.loads(plan.plan_details)
    profile_data = {'weight': current_user.profile.weight}
    return render_template('workout.html', user=current_user, workout_data=workout_data, profile=profile_data, timestamp=int(time.time()))

@app.route('/api/save_workout', methods=['POST'])
@login_required
def save_workout():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    
    new_log = WorkoutLog(day_of_week=data.get('dayOfWeek'), log_details=json.dumps(data.get('logDetails')), todays_weight=data.get('todaysWeight') if data.get('todaysWeight') else None, user_id=current_user.id)
    db.session.add(new_log)
    db.session.commit()
    
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
        structure = json.loads(plan.plan_details).get('structure', [])
        exercise_names = [item.get('details', {}).get('name', 'Unnamed Step') for item in structure]
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
    volume_labels, volume_data, exercise_progression = [], [], {}
    for log in logs:
        volume_labels.append(log.date.strftime('%b %d') + f" ({log.day_of_week[:3]})")
        total_volume = 0
        log_details = json.loads(log.log_details)
        for exercise, sets in log_details.items():
            max_e1rm = 0
            if not exercise_progression.get(exercise):
                exercise_progression[exercise] = {'labels': [], 'data': []}
            for set_num, data in sets.items():
                if set_num.isdigit():
                    try:
                        weight, reps = float(data.get('weight', 0)), int(data.get('reps', 0))
                        if weight > 0 and reps > 0:
                            total_volume += weight * reps
                            e1rm = weight / (1.0278 - (0.0278 * reps))
                            if e1rm > max_e1rm:
                                max_e1rm = e1rm
                    except (ValueError, TypeError):
                        continue
            if max_e1rm > 0:
                exercise_progression[exercise]['labels'].append(log.date.strftime('%b %d'))
                exercise_progression[exercise]['data'].append(round(max_e1rm, 1))
        volume_data.append(total_volume)
    return jsonify({
        'weight_logs': {'labels': weight_labels, 'data': weight_data},
        'volume_logs': {'labels': volume_labels, 'data': volume_data},
        'exercise_progression': exercise_progression
    })

@app.route('/admin/reset_all_data/<secret_key>')
def reset_all_data(secret_key):
    admin_secret_key = os.environ.get('ADMIN_RESET_KEY', 'resetmaster')
    if secret_key != admin_secret_key:
        return "Unauthorized", 403
    try:
        db.session.query(PreviousLog).delete()
        db.session.query(WorkoutLog).delete()
        db.session.query(WorkoutPlan).delete()
        db.session.query(UserProfile).delete()
        db.session.query(User).delete()
        db.session.commit()
        flash("All data has been reset successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {e}")
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)