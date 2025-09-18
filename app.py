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

# --- EXERCISE KNOWLEDGE BASE ---
EXERCISE_KNOWLEDGE_BASE = {
    'warmup_dynamic': [
        {'name': 'Arm Circles', 'instructions': "Spin your arms in little circles like an airplane. 20 sec forward, 20 backward."},
        {'name': 'Torso Twists', 'instructions': "Twist your body gently left and right. Pretend you're looking behind you. 30 sec."},
        {'name': 'Shoulder Rolls', 'instructions': "Lift your shoulders up and back slowly. 20 sec."},
        {'name': 'Leg Swings', 'instructions': "Swing one leg forward and back like a pendulum. Then the other leg. 15 times each."}
    ],
    'cardio': [
        {'name': 'Treadmill', 'instructions': "Walk or jog. Keep your feet moving fast. Speed 5-6 for walking, 8-10 for jogging. Incline 1-2%."},
        {'name': 'Elliptical', 'instructions': "Move your legs and arms like skating. Keep it steady, not too fast."}
    ],
    'main': {
        'chest': [
            {'name': 'Incline Chest Press', 'instructions': "Push handles up slowly. Pretend pushing a big box. Squeeze chest."},
            {'name': 'Vertical Chest Press', 'instructions': "Push straight out. Keep back flat. Don't lock elbows."},
            {'name': 'Pec Fly', 'instructions': "Open arms wide like hugging a tree. Squeeze chest when closing arms."}
        ],
        'back': [
            {'name': 'Lat Pull Down', 'instructions': "Pull bar to chest like bringing a rope. Keep tummy tight."},
            {'name': 'Long Pull Row', 'instructions': "Pull handles to tummy like rowing. Keep back straight."}
        ],
        'shoulders': [
            {'name': 'Lateral Raise Machine', 'instructions': "Lift arms sideways to shoulder height. Don't shrug."},
            {'name': 'Overhead Press Machine', 'instructions': "Push handles over head. Keep back straight."}
        ],
        'biceps': [
            {'name': 'Bicep Curls Machine', 'instructions': "Curl arms like lifting small bucket. Keep elbows still."}
        ],
        'triceps': [
            {'name': 'Seated Tricep Machine', 'instructions': "Push down slowly. Feel back of arms working."}
        ],
        'quads': [
            {'name': 'Leg Extension', 'instructions': "Push legs straight. Pretend kicking gently."}
        ],
        'hamstrings': [
            {'name': 'Seated Leg Curls', 'instructions': "Pull heels back like trying to touch bottom. Go slow."}
        ],
        'calves': [
            {'name': 'Standing Calf Raise', 'instructions': "Stand on tiptoes like ballerina. Go up and down slowly."}
        ],
        'core': [
            {'name': 'Abdominal Machine', 'instructions': "Push tummy towards knees. Don't use arms."}
        ]
    },
    'cooldown_static': [
        {'name': 'Quad Stretch', 'instructions': "Hold one leg behind like ballerina. Count 30 slowly."},
        {'name': 'Hamstring Stretch', 'instructions': "Reach for toes gently. Count 30 slowly."},
        {'name': 'Chest Stretch', 'instructions': "Open arms wide. Count 30."},
        {'name': 'Triceps Stretch', 'instructions': "Lift one arm up, bend behind head. Use other hand gently. Count 30."}
    ]
}

@app.context_processor
def inject_exercise_library():
    flat_library = []
    for cat in EXERCISE_KNOWLEDGE_BASE['main'].values():
        flat_library.extend(cat)
    unique = list({v['name']: v for v in flat_library}.values())
    return dict(EXERCISE_LIBRARY=unique)

# --- PROGRESSIVE OVERLOAD LOGIC ---
def get_progressive_overload_suggestion(exercise_name, last_log_details, rep_target):
    if not last_log_details or exercise_name not in last_log_details:
        return "<p>First time doing this exercise. Pick challenging but safe weight.</p>"

    exercise_log = last_log_details.get(exercise_name, {})
    last_weight = 0
    all_reps_met = True
    logged_sets = [data for set_num, data in exercise_log.items() if set_num.isdigit()]
    if not logged_sets:
        return "<p>Start light and focus on form!</p>"

    for set_data in logged_sets:
        try:
            reps_done = int(set_data.get('reps', 0))
            last_weight = float(set_data.get('weight', 0))
        except:
            continue
        if reps_done < rep_target:
            all_reps_met = False
            break

    if all_reps_met and last_weight > 0:
        return f"<p>Last time {last_weight}kg done. Try {last_weight + 2.5}kg now!</p>"
    elif last_weight > 0:
        return f"<p>Last time {last_weight}kg. Focus on completing reps first.</p>"
    return "<p>Start light and focus on form!</p>"

# --- AI WORKOUT PLAN GENERATION ---
def generate_ai_workout_plan(user):
    if not user or not user.profile:
        return {}
    profile = user.profile
    last_log = WorkoutLog.query.filter_by(user_id=user.id).order_by(WorkoutLog.date.desc()).first()
    try:
        last_log_details = json.loads(last_log.log_details) if last_log and last_log.log_details else {}
    except:
        last_log_details = {}
    previous_exercises = [log.exercise_name for log in user.previous_logs] if user.previous_logs else []
    focus_areas = profile.focus_areas.split(',') if profile.focus_areas else []
    days = profile.workout_days.split(',') if profile.workout_days else []
    goals = profile.physique_goal.split(',') if profile.physique_goal else []

    rep_range, rep_target = ("4 sets of 6-8 reps", 6) if 'bold' in goals or 'strength' in goals else ("3 sets of 10-12 reps", 10)
    rotation = ['Push','Pull','Legs'] if len(days) >= 4 else ['Upper Body','Lower Body','Full Body'] if len(days) == 3 else ['Full Body']
    day_map = {name:i for i,name in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
    sorted_days = sorted(days, key=lambda day: day_map.get(day, 7))
    split = {day: rotation[i % len(rotation)] for i, day in enumerate(sorted_days)}

    weekly_plan = {}
    for day_name in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
        if day_name in split:
            workout_type = split[day_name]
            workout = {"workout_name": f"{workout_type} Day", "structure": []}

            # Warm-up
            workout['structure'].append({"type": "Warm-up", "details": EXERCISE_KNOWLEDGE_BASE['cardio'][0], "duration": "5 min"})
            workout['structure'].extend([{"type":"Warm-up","details":ex,"duration":"30 sec"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['warmup_dynamic'],2)])

            # Main exercises
            exercises_to_add = []
            def get_available_exercises(muscle):
                pool = EXERCISE_KNOWLEDGE_BASE['main'].get(muscle, []) or []
                choices = [ex for ex in pool if ex['name'] not in previous_exercises] or pool
                return choices

            if workout_type == 'Push':
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), min(2,len(get_available_exercises('chest')))))
                exercises_to_add.extend(random.sample(get_available_exercises('triceps'), min(1,len(get_available_exercises('triceps')))))
            elif workout_type == 'Pull':
                exercises_to_add.extend(random.sample(get_available_exercises('back'), min(2,len(get_available_exercises('back')))))
                exercises_to_add.extend(random.sample(get_available_exercises('biceps'), min(1,len(get_available_exercises('biceps')))))
            elif workout_type in ['Legs','Lower Body']:
                exercises_to_add.extend(random.sample(get_available_exercises('quads'), min(1,len(get_available_exercises('quads')))))
                exercises_to_add.extend(random.sample(get_available_exercises('hamstrings'), min(1,len(get_available_exercises('hamstrings')))))
                exercises_to_add.extend(random.sample(get_available_exercises('calves'), min(1,len(get_available_exercises('calves')))))
            else:
                exercises_to_add.extend(random.sample(get_available_exercises('chest'), min(1,len(get_available_exercises('chest')))))
                exercises_to_add.extend(random.sample(get_available_exercises('back'), min(1,len(get_available_exercises('back')))))
                exercises_to_add.extend(random.sample(get_available_exercises('quads'), min(1,len(get_available_exercises('quads')))))

            for area in focus_areas:
                if area in EXERCISE_KNOWLEDGE_BASE['main']:
                    choices = get_available_exercises(area)
                    if choices:
                        exercises_to_add.append(random.choice(choices))

            unique_exercises = list({ex['name']:ex for ex in exercises_to_add}.values())
            for ex_obj in unique_exercises:
                ex_copy = ex_obj.copy()
                suggestion = get_progressive_overload_suggestion(ex_copy['name'], last_log_details, rep_target)
                ex_copy['instructions'] = suggestion + "<br>" + ex_copy.get('instructions','')
                workout['structure'].append({"type":"Main","details":ex_copy,"target":rep_range,"rest":"60-90 sec"})

            # Cooldown
            workout['structure'].append({"type":"Cooldown Cardio","details":EXERCISE_KNOWLEDGE_BASE['cardio'][1],"duration":"5-10 min"})
            workout['structure'].extend([{"type":"Stretching","details":ex,"duration":"30 sec"} for ex in random.sample(EXERCISE_KNOWLEDGE_BASE['cooldown_static'],2)])
            weekly_plan[day_name] = workout
        else:
            weekly_plan[day_name] = None
    return weekly_plan

# --- ROUTES ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html', timestamp=int(time.time()))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if not username or not password:
            flash("Please provide username and password.","danger")
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash("Username exists","danger")
            return redirect(url_for('signup'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('profile_setup'))
    return render_template('signup.html', timestamp=int(time.time()))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        user=User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid username or password","danger")
        return redirect(url_for('login'))
    return render_template('login.html', timestamp=int(time.time()))

@app.route('/profile_setup', methods=['GET','POST'])
@login_required
def profile_setup():
    if request.method=='POST':
        try:
            age=int(request.form.get('age'))
            height=int(request.form.get('height'))
            weight=float(request.form.get('weight'))
            gender=request.form.get('gender')
            workout_days=','.join(request.form.getlist('workout_days'))
            physique_goal=','.join(request.form.getlist('physique_goal'))
            duration=float(request.form.get('duration'))
            equipment=request.form.get('equipment') or ''
            focus_areas=','.join(request.form.getlist('focus_areas'))
        except:
            flash("Form error. Check values.","danger")
            return redirect(url_for('profile_setup'))

        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            profile.age=age
            profile.height=height
            profile.weight=weight
            profile.gender=gender
            profile.workout_days=workout_days
            profile.physique_goal=physique_goal
            profile.duration=duration
            profile.equipment=equipment
            profile.focus_areas=focus_areas
        else:
            profile=UserProfile(
                age=age, height=height, weight=weight, gender=gender,
                workout_days=workout_days, physique_goal=physique_goal,
                duration=duration, equipment=equipment, focus_areas=focus_areas,
                user_id=current_user.id
            )
            db.session.add(profile)

        # Save previous exercises
        PreviousLog.query.filter_by(user_id=current_user.id).delete()
        prev_exercises=request.form.getlist('prev_exercise')
        for ex_name in prev_exercises:
            sets=request.form.get(f"prev_{ex_name}_sets")
            reps=request.form.get(f"prev_{ex_name}_reps")
            kg=request.form.get(f"prev_{ex_name}_kg")
            try: sets_val=int(sets) if sets else None
            except: sets_val=None
            try: reps_val=int(reps) if reps else None
            except: reps_val=None
            try: kg_val=float(kg) if kg else None
            except: kg_val=None
            prev=PreviousLog(exercise_name=ex_name, sets=sets_val, reps=reps_val, kg=kg_val, user_id=current_user.id)
            db.session.add(prev)

        db.session.commit()
        flash("Profile saved.","success")
        return redirect(url_for('dashboard'))
    return render_template('profile_setup.html', timestamp=int(time.time()))

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.profile:
        flash("Complete your profile first.","info")
        return redirect(url_for('profile_setup'))

    # Generate plan if not exists
    if not current_user.workout_plans:
        new_plan=generate_ai_workout_plan(current_user)
        for day, details in new_plan.items():
            if details:
                db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=current_user.id))
        db.session.commit()

    # Prepare plan data for JS
    plan_data=[]
    for p in current_user.workout_plans:
        plan_data.append({
            "day_of_week": p.day_of_week,
            "workout_name": p.workout_name,
            "plan_details": json.loads(p.plan_details)
        })

    return render_template('dashboard.html', user=current_user, workout_plans=plan_data, timestamp=int(time.time()))

@app.route('/performance')
@login_required
def performance():
    return render_template('performance.html', timestamp=int(time.time()))

@app.route('/api/get_performance_data')
@login_required
def get_performance_data():
    logs=WorkoutLog.query.filter_by(user_id=current_user.id).order_by(WorkoutLog.date.asc()).all()
    weight_labels,weight_data,volume_labels,volume_data=[],[],[],[]
    exercise_progression={}

    for log in logs:
        if log.todays_weight is not None:
            weight_labels.append(log.date.strftime('%b %d'))
            weight_data.append(log.todays_weight)

        total_volume=0
        try: log_details=json.loads(log.log_details) if log.log_details else {}
        except: log_details={}

        for exercise, sets in (log_details.items() if isinstance(log_details, dict) else []):
            max_e1rm=0
            if exercise not in exercise_progression:
                exercise_progression[exercise]={'labels':[],'data':[]}
            for set_num, data in (sets.items() if isinstance(sets, dict) else []):
                if set_num.isdigit():
                    try:
                        weight=float(data.get('weight',0))
                        reps=int(data.get('reps',0))
                    except:
                        continue
                    if weight>0 and reps>0:
                        total_volume+=weight*reps
                        try:
                            e1rm=weight/(1.0278-(0.0278*reps))
                            if e1rm>max_e1rm: max_e1rm=e1rm
                        except: pass
            if max_e1rm>0:
                exercise_progression[exercise]['labels'].append(log.date.strftime('%b %d'))
                exercise_progression[exercise]['data'].append(round(max_e1rm,1))

        volume_labels.append(log.date.strftime('%b %d')+f" ({log.day_of_week[:3]})")
        volume_data.append(total_volume)

    return jsonify({
        'weight_logs':{'labels':weight_labels,'data':weight_data},
        'volume_logs':{'labels':volume_labels,'data':volume_data},
        'exercise_progression':exercise_progression
    })

@app.route('/api/save_workout', methods=['POST'])
@login_required
def save_workout():
    data=request.get_json()
    if not data:
        return jsonify({'status':'error','message':'Invalid data'}),400
    try:
        new_log=WorkoutLog(
            day_of_week=data.get('dayOfWeek'),
            log_details=json.dumps(data.get('logDetails') or {}),
            todays_weight=float(data.get('todaysWeight')) if data.get('todaysWeight') else None,
            user_id=current_user.id
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'status':'error','message':f'Failed: {e}'}),500

    try:
        WorkoutPlan.query.filter_by(user_id=current_user.id).delete()
        new_plan=generate_ai_workout_plan(current_user)
        for day, details in new_plan.items():
            if details:
                db.session.add(WorkoutPlan(day_of_week=day, workout_name=details['workout_name'], plan_details=json.dumps(details), user_id=current_user.id))
        db.session.commit()
    except:
        db.session.rollback()

    return jsonify({'status':'success','message':'Workout saved'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- RUN APP ---
if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
