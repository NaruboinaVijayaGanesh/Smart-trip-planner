# AI AIR TRIP PLANNER

Production-ready Flask web application for AI-assisted air trip planning with traveler and travel-agent workflows.

## 1. Project Structure

```text
Smart-trip-planner/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── agent_controller.py
│   │   ├── main_controller.py
│   │   └── traveler_controller.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── authz.py
│   │   ├── budget_service.py
│   │   ├── cache_service.py
│   │   ├── email_service.py
│   │   ├── export_service.py
│   │   ├── food_data_service.py
│   │   ├── form_service.py
│   │   ├── gemini_service.py
│   │   ├── hotel_service.py
│   │   ├── itinerary_approval_service.py
│   │   ├── ml_service.py
│   │   ├── otp_service.py
│   │   ├── place_service.py
│   │   ├── schema_service.py
│   │   ├── seed_service.py
│   │   ├── trip_service.py
│   │   ├── trip_update_approval_service.py
│   │   ├── validation_service.py
│   │   ├── weather_service.py
│   │   └── whatsapp_service.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── img/
│   │   ├── js/
│   │   │   └── app.js
│   │   └── uploads/
│   │       └── payments/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── chatbot.html
│       ├── agent/
│       │   ├── bookings.html
│       │   ├── clients.html
│       │   ├── create_trip.html
│       │   ├── dashboard.html
│       │   ├── trip_detail.html
│       │   └── trips.html
│       ├── auth/
│       │   ├── forgot_password.html
│       │   ├── login.html
│       │   ├── profile.html
│       │   └── register.html
│       ├── traveler/
│       │   ├── create_trip.html
│       │   ├── dashboard.html
│       │   ├── my_trips.html
│       │   └── trip_detail.html
│       └── partials/
│           ├── agent_sidebar.html
│           ├── phone_input.html
│           └── trip_form_fields.html
├── ml/
│   ├── __init__.py
│   ├── ml_model.py
│   ├── train_model.py
│   ├── train_food_model.py
│   ├── budget_model.joblib
│   ├── food_model_metrics.json
│   ├── model_metrics.json
│   ├── classification_report.csv
│   └── confusion_matrix.csv
├── data/
│   ├── budget_dataset.csv
│   └── food_cost_dataset.csv
├── instance/
│   └── cache/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── venv/
```

## 2. Features Implemented

### Authentication & Authorization
- Role-based authentication with Flask-Login
  - Registration with role selection (`traveler` / `agent`)
  - Secure password hashing with werkzeug
  - Email OTP verification for registration and password reset
  - Google OAuth 2 integration
  - Profile management with phone number validation

### Traveler Module
- Trip creation with multi-destination support
- AI-powered itinerary generation (day-wise with activities) via Google Gemini API
- Budget breakdown with ML-powered budget prediction
- Weather forecasts for trip destinations
- Hotel search and booking management
- Payment proof submission and tracking
- Trip feedback and ratings post-completion
- My Trips list with filtering and export functionality
- Trip sharing via WhatsApp
- Interest expression for trips

### Travel Agent Module
- Dashboard with comprehensive metrics
  - Total clients, recent clients, total trips
  - Total bookings, upcoming trips, total revenue
- Complete client CRUD operations
- Create and manage trips for clients
  - Status management (draft, sent, confirmed, in-progress, completed)
  - Service charge calculation
- Advanced trip management features
  - Manual itinerary editing with approval workflow
  - Trip status updates
  - Hotel booking management (pending/confirmed/cancelled)
  - Payment verification and confirmation
- WhatsApp integration for client communication
  - Generate WhatsApp sharing links
  - Email integration for trip summaries

### Machine Learning Features
- Budget prediction model using scikit-learn
- Food cost prediction model
- ML model training and evaluation pipeline
- Runtime integration for accurate trip budgeting

### Additional Features
- Nomini tax calculation and integration
- Dynamic pricing and cost optimization
- Email notifications for trip updates
- WhatsApp notifications for travelers and agents
- Advanced validation for locations and trip details
- Caching system for improved performance
- Export trip details (itinerary, budget breakdown)

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

1. Create and activate a virtual environment:

   **For Windows:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

   **For macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

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

### For Travelers
1. Open http://127.0.0.1:5000 and register a new account with role `Traveler`
2. Complete email OTP verification
3. Create a new trip by providing:
   - Origin location (GPS-enabled or manual entry)
   - Destinations (comma-separated)
   - Travel dates and duration
   - Budget and number of travelers
   - Travel preferences (adventure, culture, food, etc.)
4. View AI-generated day-wise itinerary
5. Check ML-predicted budget breakdown
6. View hotel recommendations
7. Complete a trip and submit feedback ratings
8. Export trip details or share via WhatsApp

### For Travel Agents
1. Open http://127.0.0.1:5000 and register a new account with role `Agent`
2. Complete email OTP verification
3. Add clients to your client list
4. Create trips for your clients with custom details
5. Manage trip status and itinerary
6. Handle hotel bookings and payment verification
7. View comprehensive dashboard with business metrics
8. Send WhatsApp updates to travelers

## 6. Environment Configuration

Create a `.env` file in the project root with:

```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=sqlite:///instance/air_trip_planner.db
GOOGLE_API_KEY=your-google-gemini-api-key
GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number
OTP_EXPIRY_MINUTES=10
```

## 7. Notes for Production Hardening

- **Security**
  - Replace default `SECRET_KEY` with a strong, random secret from environment
  - Use PostgreSQL/MySQL instead of SQLite for multi-user production workloads
  - Enable HTTPS/TLS for all connections
  - Implement rate limiting to prevent abuse
  - Add CSRF protection with Flask-WTF
  
- **Database**
  - Set up automated backups
  - Use connection pooling for database connections
  - Implement Alembic/Flask-Migrate for schema migrations
  - Regular database maintenance and optimization

- **API Integration**
  - Securely store API keys in environment variables
  - Implement API rate limiting and retry logic
  - Add comprehensive error handling for external APIs
  - Monitor API usage and costs

- **Code Quality**
  - Add comprehensive unit and integration tests
  - Implement proper route authorization tests
  - Add structured logging throughout the application
  - Implement monitoring and alerting systems
  - Use dependency scanning tools for security vulnerabilities

- **Performance**
  - Implement caching strategies (Redis)
  - Optimize database queries
  - Use CDN for static assets
  - Implement async tasks for long-running operations
  - Monitor application performance metrics
