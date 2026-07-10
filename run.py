"""
Application entry point.

    python run.py          # development
    flask --app run run    # flask CLI
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
