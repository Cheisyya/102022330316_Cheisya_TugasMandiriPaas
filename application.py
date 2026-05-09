import os
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from models import Task, db


def _default_database_url() -> str:
    # Elastic Beanstalk Linux instances can safely use /tmp for SQLite storage.
    if os.name == "nt":
        return "sqlite:///database.db"
    return "sqlite:////tmp/database.db"


application = Flask(__name__)
application.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret-key")
application.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", _default_database_url()
)
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(application)

with application.app_context():
    db.create_all()


@application.route("/", methods=["GET"])
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)


@application.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks]), 200


@application.route("/tasks", methods=["POST"])
def create_task():
    title = request.form.get("title", "").strip()
    if not title:
        abort(400, description="Title is required.")

    new_task = Task(title=title)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("index"))


@application.route("/tasks/<int:id>/complete", methods=["POST"])
def toggle_task(id: int):
    task = Task.query.get_or_404(id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for("index"))


@application.route("/tasks/<int:id>/delete", methods=["POST"])
def delete_task(id: int):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))


@application.route("/health", methods=["GET"])
def health_check():
    db.session.execute(db.text("SELECT 1"))
    return (
        jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
            }
        ),
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=False)
