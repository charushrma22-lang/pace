
from pathlib import Path
from datetime import datetime, timedelta

from flask import (
    Flask, jsonify, render_template, request,
    redirect, url_for, flash
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)

from werkzeug.security import (
    generate_password_hash, check_password_hash
)


# ==========================================
# 1. CREATE FLASK APPLICATION
# ==========================================

app = Flask(__name__)

Path(app.instance_path).mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. APPLICATION CONFIGURATION
# ==========================================

app.config["SECRET_KEY"] = "pace-development-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pace.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ==========================================
# 3. DATABASE INITIALIZATION
# ==========================================

db = SQLAlchemy()
db.init_app(app)


# ==========================================
# 4. LOGIN MANAGER
# ==========================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
# ==========================================
# USER MODEL
# ==========================================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(256),
        nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
# ==========================================
# 5. HABIT MODEL
# ==========================================

class Habit(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    completed = db.Column(db.Boolean, default=False)

# ==========================================
# HABIT COMPLETION HISTORY
# ==========================================

class HabitLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    habit_id = db.Column(
        db.Integer,
        db.ForeignKey("habit.id"),
        nullable=False
    )

    log_date = db.Column(
        db.Date,
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "habit_id",
            "log_date",
            name="unique_habit_daily_log"
        ),
    )


# ==========================================
# 6. TASK MODEL
# ==========================================

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    description = db.Column(db.String(300))

    due_date = db.Column(db.Date, nullable=True)

    priority = db.Column(
        db.String(20),
        default="Medium"
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )


# ==========================================
# 7. HOMEPAGE
# ==========================================

@app.route("/")
@login_required
def home():
    return render_template("index.html")
@app.route("/calendar")
def calendar():
    return render_template("calendar.html")
@app.route("/streaks")
def streaks():
    return render_template("streaks.html")
@app.route("/focus")
def focus():
    return render_template("focus.html")
@app.route("/analytics")
def analytics():
    return render_template("analytics.html")
@app.route("/planner")
def planner():
    return render_template("planner.html")
@app.route("/habits")
def habits():
    return render_template("habits.html")
# ==========================================
# USER SIGNUP
# ==========================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("signup"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("signup"))

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for("signup"))

        new_user = User(
            username=username,
            email=email
        )

        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")
# ==========================================
# USER LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")
# ==========================================
# USER LOGOUT
# ==========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out successfully.")

    return redirect(url_for("login"))

# ==========================================
# 8. API HEALTH CHECK
# ==========================================

@app.route("/api/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "success",
        "message": "PACE API is running!",
        "project": "PACE"
    }), 200


# ==========================================
# 9. GET ALL HABITS
# ==========================================

@app.route("/api/habits", methods=["GET"])
def get_habits():

    habits = Habit.query.order_by(Habit.id.desc()).all()

    return jsonify([
        {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "completed": habit.completed
        }
        for habit in habits
    ]), 200


# ==========================================
# 10. ADD A HABIT
# ==========================================

@app.route("/api/habits", methods=["POST"])
def add_habit():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send valid JSON data."
        }), 400

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({
            "status": "error",
            "message": "Habit name is required."
        }), 400

    description = data.get("description", "")

    if not isinstance(description, str):
        description = ""

    new_habit = Habit(
        name=name.strip(),
        description=description.strip()
    )

    db.session.add(new_habit)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Habit added successfully!",
        "habit": {
            "id": new_habit.id,
            "name": new_habit.name,
            "description": new_habit.description,
            "completed": new_habit.completed
        }
    }), 201


# ==========================================
# 11. UPDATE HABIT COMPLETION
# ==========================================



@app.route("/api/habits/<int:habit_id>", methods=["PATCH"])
def update_habit(habit_id):

    habit = db.session.get(Habit, habit_id)

    if habit is None:
        return jsonify({
            "status": "error",
            "message": "Habit not found."
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send valid JSON data."
        }), 400

    completed = data.get("completed")

    if not isinstance(completed, bool):
        return jsonify({
            "status": "error",
            "message": "Completed must be true or false."
        }), 400

    # Update today's habit status
    habit.completed = completed

    # Find today's history record
    today = datetime.now().date()

    log = HabitLog.query.filter_by(
        habit_id=habit.id,
        log_date=today
    ).first()

    # Create a new record if one doesn't exist
    if log is None:
        log = HabitLog(
            habit_id=habit.id,
            log_date=today,
            completed=completed
        )
        db.session.add(log)

    else:
        log.completed = completed

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Habit updated successfully!"
    }), 200



# ==========================================
# 12. DELETE A HABIT
# ==========================================

@app.route("/api/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):

    habit = db.session.get(Habit, habit_id)

    if habit is None:
        return jsonify({
            "status": "error",
            "message": "Habit not found."
        }), 404

    db.session.delete(habit)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Habit deleted successfully!"
    }), 200
# ==========================================
# 12A. GET HABIT HISTORY FOR A DATE
# ==========================================

@app.route("/api/habit-history", methods=["GET"])
def get_habit_history():

    date_value = request.args.get("date")

    if not date_value:
        return jsonify({
            "status": "error",
            "message": "Date is required."
        }), 400

    try:
        selected_date = datetime.strptime(
            date_value, "%Y-%m-%d"
        ).date()
    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid date format."
        }), 400

    logs = HabitLog.query.filter_by(
        log_date=selected_date
    ).all()

    return jsonify([
        {
            "habit_id": log.habit_id,
            "completed": log.completed
        }
        for log in logs
    ]), 200


# ==========================================
# 12B. SAVE HABIT COMPLETION FOR A DATE
# ==========================================

@app.route("/api/habit-history", methods=["POST"])
def save_habit_history():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send valid JSON data."
        }), 400

    habit_id = data.get("habit_id")
    date_value = data.get("date")
    completed = data.get("completed")

    if not isinstance(habit_id, int) or isinstance(habit_id, bool):
        return jsonify({
            "status": "error",
            "message": "Invalid habit ID."
        }), 400

    if not isinstance(completed, bool):
        return jsonify({
            "status": "error",
            "message": "Completed must be true or false."
        }), 400

    try:
        selected_date = datetime.strptime(
            date_value, "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid date."
        }), 400

    habit = db.session.get(Habit, habit_id)

    if habit is None:
        return jsonify({
            "status": "error",
            "message": "Habit not found."
        }), 404

    log = HabitLog.query.filter_by(
        habit_id=habit_id,
        log_date=selected_date
    ).first()

    if log is None:
        log = HabitLog(
            habit_id=habit_id,
            log_date=selected_date,
            completed=completed
        )
        db.session.add(log)
    else:
        log.completed = completed

    # Keep the existing dashboard status in sync for today only.
    if selected_date == datetime.now().date():
        habit.completed = completed

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Habit history saved successfully."
    }), 200

# ==========================================
# STREAKS AND REWARDS API
# ==========================================

@app.route("/api/streaks", methods=["GET"])
def get_streaks():

    today = datetime.now().date()

    # Get all completed habit logs
    logs = HabitLog.query.filter_by(completed=True).all()

    # Group completed dates by habit
    all_dates = set()
    habit_dates = {}

    for log in logs:
        all_dates.add(log.log_date)

        if log.habit_id not in habit_dates:
            habit_dates[log.habit_id] = set()

        habit_dates[log.habit_id].add(log.log_date)

    # Calculate overall current streak
    start_date = today

    if today not in all_dates:
        start_date = today - timedelta(days=1)

    current_streak = 0
    check_date = start_date

    while check_date in all_dates:
        current_streak += 1
        check_date -= timedelta(days=1)

    # Calculate longest overall streak
    longest_streak = 0
    streak = 0
    previous_date = None

    for log_date in sorted(all_dates):
        if previous_date is not None:
            if log_date == previous_date + timedelta(days=1):
                streak += 1
            else:
                streak = 1
        else:
            streak = 1

        longest_streak = max(longest_streak, streak)
        previous_date = log_date

    # Calculate individual habit streaks
    habit_streaks = []

    habits = Habit.query.all()

    for habit in habits:
        dates = habit_dates.get(habit.id, set())

        habit_start = today
        if today not in dates:
            habit_start = today - timedelta(days=1)

        individual_streak = 0
        check_date = habit_start

        while check_date in dates:
            individual_streak += 1
            check_date -= timedelta(days=1)

        habit_streaks.append({
            "habit_id": habit.id,
            "habit_name": habit.name,
            "current_streak": individual_streak
        })

    # Calculate unlocked rewards
    achievements = [
        {
            "name": "First Step",
            "description": "Complete your first habit",
            "unlocked": len(logs) >= 1
        },
        {
            "name": "Getting Started",
            "description": "Reach a 3-day streak",
            "unlocked": longest_streak >= 3
        },
        {
            "name": "Consistency Star",
            "description": "Reach a 7-day streak",
            "unlocked": longest_streak >= 7
        },
        {
            "name": "Two Week Champion",
            "description": "Reach a 14-day streak",
            "unlocked": longest_streak >= 14
        },
        {
            "name": "Monthly Master",
            "description": "Reach a 30-day streak",
            "unlocked": longest_streak >= 30
        }
    ]

    return jsonify({
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_completions": len(logs),
        "habit_streaks": habit_streaks,
        "achievements": achievements
    })


# ==========================================
# 13. CONVERT TASK TO JSON
# ==========================================

def task_to_dict(task):

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": (
            task.due_date.isoformat()
            if task.due_date else None
        ),
        "priority": task.priority,
        "completed": task.completed
    }


# ==========================================
# 14. GET ALL TASKS
# ==========================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    tasks = Task.query.order_by(
        Task.due_date.asc(),
        Task.id.desc()
    ).all()

    return jsonify([
        task_to_dict(task)
        for task in tasks
    ]), 200


# ==========================================
# 15. ADD A NEW TASK
# ==========================================

@app.route("/api/tasks", methods=["POST"])
def add_task():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send valid JSON data."
        }), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({
            "status": "error",
            "message": "Task title is required."
        }), 400

    description = data.get("description", "")

    if not isinstance(description, str):
        description = ""

    priority = data.get("priority", "Medium")

    if priority not in ["Low", "Medium", "High"]:
        return jsonify({
            "status": "error",
            "message": "Invalid task priority."
        }), 400

    due_date = None
    date_value = data.get("due_date")

    if date_value:
        try:
            due_date = datetime.strptime(
                date_value, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid due date."
            }), 400

    new_task = Task(
        title=title.strip(),
        description=description.strip(),
        due_date=due_date,
        priority=priority
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Task added successfully!",
        "task": task_to_dict(new_task)
    }), 201


# ==========================================
# 16. UPDATE A TASK
# ==========================================

@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_apptask(task_id):

    task = db.session.get(Task, task_id)

    if task is None:
        return jsonify({
            "status": "error",
            "message": "Task not found."
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send valid JSON data."
        }), 400

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return jsonify({
                "status": "error",
                "message": "Task title cannot be empty."
            }), 400

        task.title = data["title"].strip()

    if "description" in data:
        if not isinstance(data["description"], str):
            return jsonify({
                "status": "error",
                "message": "Invalid description."
            }), 400

        task.description = data["description"].strip()

    if "priority" in data:
        if data["priority"] not in ["Low", "Medium", "High"]:
            return jsonify({
                "status": "error",
                "message": "Invalid priority."
            }), 400

        task.priority = data["priority"]

    if "due_date" in data:
        if data["due_date"]:
            try:
                task.due_date = datetime.strptime(
                    data["due_date"], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "Invalid due date."
                }), 400
        else:
            task.due_date = None

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            return jsonify({
                "status": "error",
                "message": "Completed must be true or false."
            }), 400

        task.completed = data["completed"]

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Task updated successfully!",
        "task": task_to_dict(task)
    }), 200


# ==========================================
# 17. DELETE A TASK
# ==========================================

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):

    task = db.session.get(Task, task_id)

    if task is None:
        return jsonify({
            "status": "error",
            "message": "Task not found."
        }), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Task deleted successfully!"
    }), 200


# ==========================================
# FOCUS SESSION API
# ==========================================

@app.route("/api/focus-sessions", methods=["GET", "POST"])
def focus_sessions():

    if request.method == "POST":
        data = request.get_json()

        duration = data.get("duration_minutes")

        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            return jsonify({"error": "Invalid session duration"}), 400

        session = FocusSession(duration_minutes=duration)

        db.session.add(session)
        db.session.commit()

        return jsonify({
            "message": "Focus session saved successfully",
            "id": session.id
        }), 201

    sessions = FocusSession.query.order_by(
        FocusSession.completed_at.desc()
    ).all()

    total_sessions = len(sessions)
    total_minutes = sum(
        session.duration_minutes for session in sessions
    )

    return jsonify({
        "total_sessions": total_sessions,
        "total_minutes": total_minutes
    })


# ==========================================
# ANALYTICS API
# ==========================================

@app.route("/api/analytics", methods=["GET"])
def get_analytics():

    today = datetime.now().date()

    # Total habits
    total_habits = Habit.query.count()

    # Total completed habit logs
    habit_completions = HabitLog.query.filter_by(
        completed=True
    ).count()

    # Task statistics
    total_tasks = Task.query.count()

    completed_tasks = Task.query.filter_by(
        completed=True
    ).count()

    # Focus statistics
    focus_sessions = FocusSession.query.all()

    focus_minutes = sum(
        session.duration_minutes for session in focus_sessions
    )

    # Weekly habit progress
    weekly_progress = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        completed_count = HabitLog.query.filter_by(
            log_date=day,
            completed=True
        ).count()

        weekly_progress.append({
            "day": day.strftime("%a"),
            "completed": completed_count
        })

    return jsonify({
        "total_habits": total_habits,
        "habit_completions": habit_completions,
        "tasks_completed": completed_tasks,
        "total_tasks": total_tasks,
        "focus_minutes": focus_minutes,
        "weekly_progress": weekly_progress
    })


# ==========================================
# 18. CREATE DATABASE TABLES
# ==========================================

with app.app_context():
    db.create_all()


# ==========================================
# 19. RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)



   