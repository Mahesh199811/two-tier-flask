from flask import Flask, jsonify, request, render_template_string
import mysql.connector
import os

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppassword"),
    "database": os.getenv("DB_NAME", "appdb"),
    "autocommit": True,
}

HTML_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Task Manager</title>
    <style>
      body { font-family: Arial, sans-serif; background: #f3f6fb; margin: 0; padding: 30px; }
      .container { max-width: 980px; margin: 0 auto; background: white; padding: 24px; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.08); }
      h1 { color: #111827; }
      .topbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
      form { display: grid; grid-template-columns: 1.2fr 2fr 120px 120px; gap: 12px; margin: 20px 0; }
      input, textarea, select, button { padding: 12px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 14px; }
      button { cursor: pointer; }
      .primary { background: #2563eb; color: #fff; border: none; }
      .secondary { background: #e5e7eb; color: #111827; border: none; }
      .danger { background: #dc2626; color: white; border: none; }
      table { width: 100%; border-collapse: collapse; margin-top: 12px; }
      th, td { border-bottom: 1px solid #e5e7eb; padding: 12px; text-align: left; vertical-align: top; }
      .status { display: inline-block; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; }
      .pending { background: #fef3c7; color: #92400e; }
      .done { background: #dcfce7; color: #166534; }
      .error { color: #b91c1c; margin-top: 10px; }
      .success { color: #166534; margin-top: 10px; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="topbar">
        <h1>Task Manager</h1>
      </div>

      <form id="task-form">
        <input id="title" name="title" placeholder="Task title" required>
        <textarea id="description" name="description" placeholder="Task description"></textarea>
        <select id="status" name="status">
          <option value="pending">Pending</option>
          <option value="done">Done</option>
        </select>
        <button class="primary" type="submit">Add Task</button>
      </form>

      <div id="message"></div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for task in tasks %}
          <tr data-id="{{ task.id }}">
            <td>{{ task.id }}</td>
            <td>{{ task.title }}</td>
            <td>{{ task.description or '-' }}</td>
            <td><span class="status {{ task.status }}">{{ task.status }}</span></td>
            <td>{{ task.created_at }}</td>
            <td>
              <button class="secondary edit-btn" data-id="{{ task.id }}" data-title="{{ task.title }}" data-description="{{ task.description or '' }}" data-status="{{ task.status }}">Edit</button>
              <button class="danger delete-btn" data-id="{{ task.id }}">Delete</button>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <script>
      const form = document.getElementById('task-form');
      const messageBox = document.getElementById('message');
      const titleInput = document.getElementById('title');
      const descriptionInput = document.getElementById('description');
      const statusInput = document.getElementById('status');

      function showMessage(message, type) {
        messageBox.className = type;
        messageBox.textContent = message;
      }

      form.addEventListener('submit', async function (event) {
        event.preventDefault();

        const payload = {
          title: titleInput.value.trim(),
          description: descriptionInput.value.trim(),
          status: statusInput.value
        };

        const response = await fetch('/api/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
          showMessage(result.error || 'Something went wrong', 'error');
          return;
        }

        showMessage('Task added successfully!', 'success');
        form.reset();
        location.reload();
      });

      document.addEventListener('click', async function (event) {
        const target = event.target;

        if (target.classList.contains('delete-btn')) {
          const taskId = target.dataset.id;
          const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
          const result = await response.json();

          if (!response.ok) {
            showMessage(result.error || 'Delete failed', 'error');
            return;
          }

          showMessage('Task deleted successfully!', 'success');
          location.reload();
        }

        if (target.classList.contains('edit-btn')) {
          const taskId = target.dataset.id;
          const title = target.dataset.title;
          const description = target.dataset.description;
          const status = target.dataset.status;

          titleInput.value = title;
          descriptionInput.value = description;
          statusInput.value = status;

          const submitButton = form.querySelector('button[type="submit"]');
          submitButton.textContent = 'Update Task';
          submitButton.dataset.taskId = taskId;
          submitButton.dataset.mode = 'edit';
          showMessage('Editing task. Update the values and save.', 'success');
        }
      });

      form.addEventListener('submit', async function (event) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton.dataset.mode === 'edit') {
          event.preventDefault();
          const taskId = submitButton.dataset.taskId;
          const payload = {
            title: titleInput.value.trim(),
            description: descriptionInput.value.trim(),
            status: statusInput.value
          };

          const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const result = await response.json();

          if (!response.ok) {
            showMessage(result.error || 'Update failed', 'error');
            return;
          }

          submitButton.textContent = 'Add Task';
          delete submitButton.dataset.taskId;
          delete submitButton.dataset.mode;
          form.reset();
          showMessage('Task updated successfully!', 'success');
          location.reload();
        }
      });
    </script>
  </body>
</html>
"""


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.close()
    connection.close()


@app.route("/")
def home():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC"
    )
    tasks = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template_string(HTML_PAGE, tasks=tasks)


@app.route("/health")
def health():
    return {"status": "healthy"}


@app.route("/db")
def database():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        cursor.close()
        connection.close()
        return {"database": "connected", "mysql_version": version[0]}
    except Exception as exc:
        return {"database": "connection failed", "error": str(exc)}, 500


@app.route("/api/tasks", methods=["GET", "POST"])
def tasks_collection():
    if request.method == "GET":
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC")
        tasks = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(tasks)

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    status = (data.get("status") or "pending").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    if status not in {"pending", "done"}:
        return jsonify({"error": "Status must be pending or done"}), 400

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s)",
            (title, description, status),
        )
        task_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return jsonify({
            "id": task_id,
            "title": title,
            "description": description,
            "status": status,
        }), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/tasks/<int:task_id>", methods=["PUT", "DELETE"])
def task_detail(task_id):
    if request.method == "DELETE":
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            cursor.close()
            connection.close()
            return jsonify({"message": "Task deleted successfully"})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    status = (data.get("status") or "pending").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    if status not in {"pending", "done"}:
        return jsonify({"error": "Status must be pending or done"}), 400

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tasks SET title=%s, description=%s, status=%s WHERE id=%s",
            (title, description, status, task_id),
        )
        cursor.close()
        connection.close()
        return jsonify({"id": task_id, "title": title, "description": description, "status": status})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
