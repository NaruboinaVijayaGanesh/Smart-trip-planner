import os

from app import create_app
from app.extensions import db  

app = create_app()

# 👇 ADD THIS BLOCK
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug_mode, use_reloader=False, threaded=False)
