# AI Life Coach Application

## Overview

This is a comprehensive AI Life Coach application built with Flask that provides personalized life guidance, goal tracking, habit management, and wellbeing analytics. The application uses OpenAI's GPT-4 model to provide intelligent coaching conversations while maintaining persistent memory of user interactions and progress.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **API Integration**: OpenAI GPT-4 for conversational AI
- **Data Storage**: JSON-based file storage (`life_memory.json`)
- **Server**: Gunicorn for production deployment
- **Security**: Custom security module with rate limiting, authentication, and monitoring

### Frontend Architecture
- **UI Framework**: Bootstrap with dark theme
- **JavaScript**: Vanilla JS for chat interface and dynamic interactions
- **Styling**: Custom CSS with responsive design
- **Icons**: Font Awesome for UI elements

### Modular Components
- **Core Application** (`app.py`): Main Flask application with chat endpoints
- **Security Module** (`security.py`): Rate limiting, authentication, and system monitoring
- **Admin Dashboard** (`admin_dashboard.py`): System management and analytics
- **Analytics Engine** (`advanced_analytics.py`): User behavior analysis and insights
- **Notification System** (`notification_system.py`): Alert and reminder management
- **Auto-Updater** (`auto_updater.py`): System maintenance and updates
- **Collaboration Tools** (`collaboration_tools.py`): Sharing and social features

## Key Components

### Memory System
The application maintains persistent user memory through a JSON-based storage system that tracks:
- Life events and conversations
- Goals and achievements
- Mood history
- Habits and milestones
- Action items and reflections
- Warnings and insights

### Security Features
- Rate limiting (60 requests per minute)
- IP-based tracking with privacy hashing
- Failed attempt monitoring
- Session token generation
- Auto-backup functionality
- System health monitoring

### Admin Dashboard
Provides comprehensive system oversight including:
- System health metrics
- Security monitoring
- User activity analytics
- Real-time performance data
- Maintenance controls

### Analytics Engine
Advanced analytics capabilities for:
- Engagement metrics
- Wellbeing analysis
- Productivity tracking
- Habit formation patterns
- Goal achievement rates
- Behavioral insights

## Data Flow

1. **User Interaction**: Users send messages through the web interface
2. **Security Check**: Rate limiting and security validation
3. **Memory Loading**: Current user memory is loaded from JSON storage
4. **AI Processing**: OpenAI API processes the message with context
5. **Memory Update**: New interactions are saved to persistent storage
6. **Response Delivery**: AI response is returned to the user interface
7. **Analytics Update**: User behavior data is processed for insights

## External Dependencies

### Core Dependencies
- **OpenAI**: GPT-4 API for conversational AI
- **Flask**: Web framework and routing
- **Gunicorn**: WSGI HTTP server

### Additional Dependencies
- **NumPy**: Numerical computations for analytics
- **Requests**: HTTP library for external API calls
- **Schedule**: Task scheduling for maintenance
- **Cryptography**: Security and encryption utilities
- **PyJWT**: JSON Web Token handling
- **Psutil**: System monitoring

### Environment Variables
- `OPENAI_API_KEY`: Required for AI functionality
- `SESSION_SECRET`: For session management security

## Deployment Strategy

### Development Environment
- Uses Flask's development server
- File-based JSON storage for simplicity
- Hot reloading enabled for development

### Production Deployment
- **Server**: Gunicorn with autoscale deployment target
- **Port Configuration**: Internal port 5000, external port 80
- **Process Management**: Parallel workflow execution
- **Health Checks**: Automatic port monitoring

### Scaling Considerations
- File-based storage suitable for single-user applications
- Database migration path available for multi-user scaling
- Modular architecture supports horizontal scaling
- Admin dashboard provides monitoring for performance optimization

## Changelog

- June 16, 2025. Initial setup
- June 26, 2025. Successfully migrated from Replit Agent to standard Replit environment

## Migration Summary (June 26, 2025)

### Changes Made During Migration
- **Database Integration**: Migrated from JSON-only storage to PostgreSQL database with fallback to JSON
- **Security Improvements**: Removed access logging code that was causing security issues
- **Import Structure**: Fixed circular import issues between app.py and models.py
- **Session Management**: Properly configured Flask sessions with SESSION_SECRET environment variable
- **Authentication**: Maintained Flask-Login integration with database-backed user management
- **Default User**: Created default user account (username: Ervin, password: Quantum210)

### Current Status  
- Application successfully running on Replit with PostgreSQL database
- **DIRECT ACCESS ENABLED** - No login required, immediate access to all features
- All core functionality preserved including AI chat, goal tracking, and analytics
- Admin dashboard fully functional with system monitoring
- Advanced analytics, notifications, and collaboration tools restored
- All security features and performance optimizations active
- Migration completed successfully with full accessibility restored

## User Preferences

Preferred communication style: Simple, everyday language.