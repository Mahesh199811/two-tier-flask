from flask import Flask
import mysql.connector
import os

app = Flask(__name__)


@app.route("/")
def home():
    return "Two-Tier Flask Application v2 - CI/CD Working!"


@app.route("/health")
def health():
    return {
        "status": "healthy"
    }


@app.route("/db")
def database():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "mysql"),
            user=os.getenv("DB_USER", "appuser"),
            password=os.getenv("DB_PASSWORD", "apppassword"),
            database=os.getenv("DB_NAME", "appdb")
        )

        cursor = connection.cursor()

        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "database": "connected",
            "mysql_version": version[0]
        }

    except Exception as e:
        return {
            "database": "connection failed",
            "error": str(e)
        }, 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
