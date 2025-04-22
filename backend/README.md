# Dana AI Platform - Backend

This directory contains the backend code for the Dana AI Platform.

## Structure

- `main.py`: Main application entry point
- `routes/`: API routes and controllers
- `utils/`: Utility functions and helpers
- `models/`: Database models
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, images)
- `migrations/`: Database migration scripts

## Running the backend

```bash
cd backend
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```
