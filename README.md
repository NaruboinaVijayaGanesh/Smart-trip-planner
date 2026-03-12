# AI AIR TRIP PLANNER

Production-ready Flask web application for AI-assisted air trip planning with traveler and travel-agent workflows.

## 1. Project Structure

```text
atp/
  app/
    __init__.py
    config.py
    extensions.py
    controllers/
      auth_controller.py
      main_controller.py
      traveler_controller.py
      agent_controller.py
    models/
      entities.py
    services/
      authz.py
      form_service.py
      trip_service.py
      budget_service.py
      hotel_service.py
      weather_service.py
      ml_service.py
      seed_service.py
    templates/
      base.html
      index.html
      auth/
      traveler/
      agent/
      partials/
    static/
      css/style.css
      js/app.js
  ml/
    ml_model.py
    train_model.py
  data/
    budget_dataset.csv
  run.py
  requirements.txt
```

## 2. Features Implemented

- Role-based authentication with Flask-Login
  - Registration with role selection (`traveler` / `agent`)
  - Secure password hashing
  - Role-based dashboard redirection
- Traveler module
  - Trip creation with multi-destination support
  - AI itinerary generation (day-wise with activities)
  - Budget breakdown and ML predicted budget
  - My Trips list, details, regenerate, delete
- Travel Agent module
  - Dashboard metrics (clients, trips, bookings, revenue)
  - Client CRUD
  - Create trip for client with service charge and status
  - Trip management, manual itinerary edits, status updates
  - Hotel booking workflow (pending/confirmed/cancelled + paid/pending)
  - WhatsApp share link and email structure
- Machine learning integration (Option B)
  - Regression model using scikit-learn
  - dataset included
  - Train/save/load pipeline
  - Runtime budget prediction integrated into trip calculations

## 3. Database Models

Implemented SQLAlchemy models with relationships and `created_at` timestamps:

- `User`
- `Client`
- `Trip`
- `Destination`
- `Itinerary`
- `Hotel`
- `Booking`
- `Payment`
- `Activity`

## 4. Step-by-Step Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Train ML model manually:

```bash
python -m ml.train_model
```

4. Initialize database and hotel seed data:

```bash
flask --app run.py init-db
```

5. Run the app:

```bash
python run.py
```

6. Open in browser:

```text
http://127.0.0.1:5000
```

## 5. Default Workflow

1. Register two accounts: one `Traveler`, one `Travel Agent`.
2. Login as traveler to generate trips and review itineraries.
3. Login as agent to add clients, create client trips, and manage bookings.

## 6. Notes for Production Hardening

- Replace default `SECRET_KEY` with a strong secret from environment.
- Use PostgreSQL/MySQL instead of SQLite for multi-user production workloads.
- Add CSRF protection (Flask-WTF), rate limiting, and structured logging.
- Add automated tests (unit + integration + route authorization tests).
- Add Alembic/Flask-Migrate for schema migrations.
