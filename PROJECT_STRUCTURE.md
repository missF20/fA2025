# Dana AI Platform - Project Structure

This document describes the improved structure of the Dana AI Platform.

## Overview

The project follows a clean organization with clear separation of frontend and backend components:

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
  ├── .replit            # Replit configuration
  └── README.md          # Project documentation
```

## Advantages of This Structure

1. **Clear Separation of Concerns**: Backend and frontend code are clearly separated, making it easier to understand and maintain.

2. **Improved Maintainability**: Files are organized based on their function, making it easier to find and modify code.

3. **Better Dependency Management**: Frontend and backend dependencies are managed independently, reducing conflicts.

4. **Simpler Deployment**: Backend and frontend can be deployed independently or together as needed.

5. **Backward Compatibility**: The existing entry point (`main.py`) continues to work, ensuring no disruption during the transition.

## Running the Application

### Backend

```bash
cd backend
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Frontend

```bash
cd frontend
npm run dev
```

### Both Together

You can run both together using:

```bash
python run.py
```

## Important Notes

1. **Port Configuration**: The backend runs on port 5000, and the frontend runs on port 5173. Make sure these ports are available.

2. **Environment Variables**: All environment variables are defined in the `.env` file at the root level.

3. **Database Migrations**: Database migrations are stored in the `backend/migrations` directory.

4. **API Documentation**: API routes are documented in `backend/routes/__init__.py`.

5. **Authentication**: The authentication system is implemented in `backend/utils/auth.py`.

## Transition Period

During the transition to this new structure, both the old and new structures will work simultaneously. The `main.py` file at the root level is a proxy that imports the app from `backend/main.py`.

## Next Steps

1. **Complete Migration**: Move all existing routes, models, and utility functions to the new structure.

2. **Update Import Statements**: Update import statements in all files to reflect the new structure.

3. **Update Documentation**: Update all documentation to reflect the new structure.

4. **Remove Legacy Code**: Once the migration is complete, remove any legacy code that is no longer needed.