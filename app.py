
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


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
    return None


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


# ==========================================
# 7. HOMEPAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


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

    habit.completed = completed
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
def update_task(task_id):

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
# 18. CREATE DATABASE TABLES
# ==========================================

with app.app_context():
    db.create_all()


# ==========================================
# 19. RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)



   