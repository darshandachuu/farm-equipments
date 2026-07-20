# Farm Equipment Rental System

A full-stack web application connecting farmers with equipment owners for agricultural equipment rental.

## Tech Stack

- **Backend:** Python 3.10+, Flask 3.0
- **Database:** SQLite (via Flask-SQLAlchemy)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Auth:** Flask-Login, Flask-WTF (CSRF)

## Quick Start

```bash
# 1. Navigate to project directory
cd farm-equipment-rental

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (auto-seeds database)
python run.py
```

Open **http://localhost:5000** in your browser.

## Login Credentials

| Role    | Email               | Password |
|---------|---------------------|----------|
| Admin   | admin@farmrent.com  | admin123 |
| Farmer  | rahul@gmail.com     | pass123  |
| Owner   | mahesh@gmail.com    | pass123  |

## Project Structure

```
farm-equipment-rental/
├── app/
│   ├── models/         # SQLAlchemy models
│   ├── routes/         # Blueprint route handlers
│   └── utils/          # Helper functions
├── templates/          # Jinja2 HTML templates
│   ├── auth/           # Login, Register, Profile
│   ├── farmer/         # Farmer dashboard & features
│   ├── owner/          # Owner dashboard & features
│   ├── admin/          # Admin dashboard & features
│   ├── payment/        # Payment & invoice
│   ├── reports/        # Admin reports
│   └── includes/       # Sidebar components
├── static/
│   ├── css/            # Custom styles
│   ├── js/             # Custom JavaScript
│   └── uploads/        # Uploaded files
├── instance/           # SQLite database
├── config.py           # App configuration
├── run.py              # Entry point with seed data
└── requirements.txt    # Python dependencies
```

## Features

- **3 User Roles:** Farmer, Equipment Owner, Administrator
- **Equipment CRUD:** Add, edit, delete, search, filter equipment
- **Booking System:** Request, approve/reject, track bookings
- **Payment Tracking:** Record payments, generate invoices
- **Admin Reports:** Equipment usage, revenue, bookings, user activity
- **Security:** Password hashing, CSRF protection, prepared queries
- **Responsive Design:** Works on desktop, tablet, and mobile

## Deployment

### Render
1. Push to GitHub
2. Create a Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn run:app`
5. Add `gunicorn` to requirements.txt for production

### PythonAnywhere
1. Upload files
2. Create virtualenv and install requirements
3. Configure WSGI to point to `run.py`
4. Set up static files mapping
