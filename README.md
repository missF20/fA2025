# Dana AI Platform

Dana AI is a comprehensive AI-powered knowledge management platform with robust system integration and intelligent document processing capabilities.

## Project Structure

The project follows a clean and modular architecture:

```
dana-ai/
  ├── backend/           # Backend Python code
  │   ├── main.py        # Main application entry point
  │   ├── models/        # Database models
  │   ├── routes/        # API routes and blueprints
  │   ├── utils/         # Utility functions and helpers
  │   ├── templates/     # HTML templates
  │   └── static/        # Static files
  │
  ├── frontend/          # React+TypeScript frontend
  │   ├── src/           # Source code
  │   ├── public/        # Public assets
  │   ├── package.json   # Frontend dependencies
  │   └── vite.config.ts # Vite configuration
  │
  ├── main.py            # Proxy to backend/main.py for compatibility
  ├── .env               # Environment variables
  └── run.py             # Utility to run both frontend and backend
```

## Setup and Installation

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+

### Environment Setup

1. Clone the repository
2. Set up a Python virtual environment (optional)
3. Install dependencies:
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd frontend
   npm install
   ```
4. Configure environment variables in `.env`

## Running the Application

### Backend Only

```bash
cd backend
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Frontend Only

```bash
cd frontend
npm run dev
```

### Both Together

```bash
python run.py
```

## API Documentation

The API is organized into the following namespaces:

- `/api/status` - API status endpoint
- `/api/integrations` - Integration management endpoints
- `/api/max-direct` - Legacy compatibility endpoints

### Authentication

API authentication is handled through JWT tokens. 
Include the token in the `Authorization` header as `Bearer <token>`.

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

## Port Configuration

- Backend: Runs on port 5000
- Frontend: Runs on port 5173

## Database Structure

The database schema is defined in the models modules. Key models include:

- `User`: Authentication and user management
- `IntegrationConfig`: Integration settings and status
- `KnowledgeFile`: Knowledge base file storage
- `TokenUsage`: AI token usage tracking

## Known Issues and Limitations

- Some import paths may need adjustment if you move files
- Frontend proxy configuration may need updates based on deployment
- PostgreSQL connection requires proper environment variables

## Development Guidelines

1. Keep backend and frontend code clearly separated
2. Use the blueprint system for organizing routes
3. Follow SQLAlchemy patterns for database access
4. Maintain RESTful API design
5. Keep environment variables in .env file, not hardcoded