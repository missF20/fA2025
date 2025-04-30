# Dana AI Platform Dependency Management

## Overview
This document outlines the dependency management strategy for the Dana AI platform, including key dependencies, update procedures, and security recommendations.

## Key Dependencies

### Core Web Framework
- **Flask**: Web framework (v2.0.0+)
- **Flask-CORS**: Cross-origin resource sharing (v3.0.10+)
- **Flask-Login**: User session management (v0.6.0+)
- **Flask-Limiter**: Rate limiting for APIs (v3.0.0+)
- **Flask-SocketIO**: WebSocket support (v5.0.0+)
- **Flask-SQLAlchemy**: ORM for database (v3.0.0+)
- **Flask-WTF**: Form validation and CSRF protection (v1.0.0+)
- **Gunicorn**: WSGI HTTP Server (v20.1.0+)
- **Werkzeug**: WSGI utilities (v2.0.0+)

### Database
- **SQLAlchemy**: SQL toolkit and ORM (v2.0.0+)
- **psycopg2-binary**: PostgreSQL adapter (v2.9.0+)
- **Alembic**: Database migration tool (v1.7.0+)
- **PyMongo**: MongoDB client (v4.0.0+)
- **Motor**: Async MongoDB client (v3.0.0+)
- **AsyncPG**: Async PostgreSQL client (v0.24.0+)
- **aiomysql**: Async MySQL client (v0.1.0+)
- **aioodbc**: Async ODBC client (v0.4.0+)

### Authentication & Security
- **python-jose**: JavaScript Object Signing and Encryption (v3.3.0+)
- **PyJWT**: JSON Web Token implementation (v2.0.0+)
- **email-validator**: Email validation (v1.1.0+)

### API Clients
- **OpenAI**: OpenAI API client (v1.0.0+)
- **Anthropic**: Anthropic API client (v0.2.0+)
- **Supabase**: Supabase client (v0.7.0+)
- **Slack SDK**: Slack API client (v3.0.0+)

### Document Processing
- **python-docx**: Word document processing (v0.8.0+)
- **docx**: Alternative Word document processing (v0.2.0+)
- **PyPDF2**: PDF processing (v2.0.0+)

### Utilities
- **Routes**: URL routing (v2.5.0+)
- **Requests**: HTTP client (v2.25.0+)
- **AIOHTTP**: Async HTTP client (v3.8.0+)

## Frontend Dependencies
- **React**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Frontend build tool
- **React-Beautiful-DnD**: Drag-and-drop functionality

## Dependency Management Tools

The Dana AI platform includes several tools for managing dependencies:

1. **check_dependencies.py**: A simple script to check for outdated packages and vulnerabilities
2. **manage_dependencies.py**: A comprehensive dependency management utility
3. **scheduled_dependency_update.py**: Automated dependency checks and updates on a schedule
4. **configure_dependency_notifications.py**: Configure notification settings for dependency issues
5. **generate_dependency_changelog.py**: Generate changelog of dependency updates
6. **generate_dependency_tests.py**: Generate tests for updated dependencies

### Using manage_dependencies.py

The dependency management utility provides four commands:

1. **Scan**: Check for outdated packages and vulnerabilities
   ```
   python manage_dependencies.py scan
   ```

2. **Update**: Update packages based on priority level
   ```
   python manage_dependencies.py update --priority [high|medium|all]
   ```

3. **Report**: Generate a detailed dependency health report
   ```
   python manage_dependencies.py report
   ```

4. **Update Requirements**: Update the requirements.txt file with latest versions
   ```
   python manage_dependencies.py update-requirements
   ```

### Automated Dependency Checks

The scheduled dependency update script can be run in three modes:

1. **Daily**: Check for security vulnerabilities
   ```
   python scheduled_dependency_update.py --mode=daily
   ```

2. **Weekly**: Apply security updates
   ```
   python scheduled_dependency_update.py --mode=weekly
   ```

3. **Monthly**: Generate comprehensive dependency report
   ```
   python scheduled_dependency_update.py --mode=monthly
   ```

### Dependency Notifications

The platform includes a comprehensive notification system for dependency vulnerabilities:

1. **Email Notifications**: Get alerts via email when critical vulnerabilities are detected
2. **Slack Notifications**: Receive alerts in Slack for security issues
3. **File-based Notifications**: All alerts are saved to the filesystem for audit purposes

Configure notifications with:
```
python configure_dependency_notifications.py
```

### Dependency Changelog

Generate a changelog of dependency updates with:
```
python generate_dependency_changelog.py --days=30 --output=dependency_changelog.md
```

### Dependency Tests

Generate tests for updated dependencies with:
```
python generate_dependency_tests.py --output=tests/dependencies
```

## Best Practices for Dependency Management

1. **Regular Scans**: Run dependency scans weekly to identify outdated packages and vulnerabilities
   ```
   python manage_dependencies.py scan
   ```

2. **Security Updates**: Prioritize security updates immediately
   ```
   python manage_dependencies.py update --priority high
   ```

3. **Comprehensive Updates**: Schedule regular comprehensive updates (monthly)
   ```
   python manage_dependencies.py update --priority all
   ```

4. **Dependency Documentation**: Keep this document updated when adding new dependencies

5. **Testing**: Always test application thoroughly after dependency updates

6. **Version Pinning**: Pin specific versions for stability, but update regularly

7. **Security Alerts**: Configure security alert systems for critical dependencies

8. **Changelog**: Maintain a changelog of dependency updates for audit purposes

9. **Automated Tests**: Generate and run tests for updated dependencies

## Update Procedure

1. Create a backup of the current environment
2. Run the dependency scan to identify needed updates
   ```
   python manage_dependencies.py scan
   ```
3. Update high-priority dependencies first
   ```
   python manage_dependencies.py update --priority high
   ```
4. Generate tests for updated dependencies
   ```
   python generate_dependency_tests.py
   ```
5. Run the generated tests to verify functionality
   ```
   python tests/dependencies/run_python_tests.py
   ```
6. Update remaining dependencies if tests pass
   ```
   python manage_dependencies.py update --priority all
   ```
7. Run the tests again to verify all functionality
8. Generate a changelog of the updates
   ```
   python generate_dependency_changelog.py
   ```
9. Document the update in release notes

## Vulnerability Management

The dependency management utility checks for known vulnerabilities in packages and automatically sends notifications. When vulnerabilities are identified:

1. Verify if the vulnerability affects the specific usage in the Dana AI platform
2. Update the affected package immediately if exploitable
   ```
   python manage_dependencies.py update --packages=vulnerable_package
   ```
3. Consider implementing mitigations if immediate update is not possible
4. Document any known vulnerabilities and mitigations in the changelog
   ```
   python generate_dependency_changelog.py
   ```

## Automated Dependency Management

Set up scheduled tasks to automate dependency management:

1. **Daily Vulnerability Checks**:
   ```
   0 8 * * * python /path/to/scheduled_dependency_update.py --mode=daily
   ```

2. **Weekly Security Updates**:
   ```
   0 7 * * 1 python /path/to/scheduled_dependency_update.py --mode=weekly
   ```

3. **Monthly Dependency Reports**:
   ```
   0 6 1 * * python /path/to/scheduled_dependency_update.py --mode=monthly
   ```

You can set up these schedules automatically using:
```
python configure_dependency_notifications.py --cron
```

## Configuration for Notifications

Configure email and Slack notifications for security vulnerabilities:

1. Setup email notifications:
   ```
   python configure_dependency_notifications.py --email
   ```

2. Setup Slack notifications:
   ```
   python configure_dependency_notifications.py --slack
   ```

3. Test notification configuration:
   ```
   python configure_dependency_notifications.py --test
   ```

## Contact

For dependency-related issues or questions, contact the Dana AI platform administrators.