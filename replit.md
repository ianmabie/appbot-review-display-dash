# App Review Webhook Receiver

## Overview

This is a real-time webhook receiver application designed to capture, parse, and analyze app reviews from external sources. The system provides a clean dashboard interface for viewing reviews with advanced filtering capabilities, live updates via WebSocket connections, and automatic data management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Python 3.11
- **Database ORM**: SQLAlchemy for database interactions
- **Real-time Communication**: Flask-SocketIO for WebSocket connections
- **Production Server**: Gunicorn with Eventlet worker for async support

### Frontend Architecture
- **Technology**: Vanilla HTML5, CSS3, and JavaScript
- **Real-time Updates**: Socket.IO client for WebSocket communication
- **UI Enhancements**: Canvas-confetti library for celebratory animations
- **Responsive Design**: CSS Grid layout with mobile-first approach

### Database Design
- **Primary Database**: PostgreSQL (configured via DATABASE_URL environment variable)
- **Connection Management**: Connection pooling with automatic reconnection and timeout handling
- **Data Retention**: Auto-cleanup mechanism maintaining only 100 most recent reviews

## Key Components

### Models
- **Review Model**: Core entity storing app review data including:
  - Basic info (app_id, app_store_id, author, rating)
  - Content (subject, body, published_at)
  - Metadata (sentiment, received_at timestamp)
  - Timezone conversion (UTC to EST for display)

### Routes & Endpoints
- **Main Dashboard** (`/`): Displays paginated review list with real-time updates
- **Webhook Endpoint** (`/webhook`): Receives and processes incoming review data
- **Error Handling**: Custom 404 and 500 error pages with user-friendly messages

### Real-time Features
- **Live Notifications**: WebSocket-based updates when new reviews arrive
- **Confetti Celebrations**: Visual feedback for new review notifications
- **State Persistence**: Review filter preferences maintained across sessions

## Data Flow

1. **Webhook Reception**: External services POST review data to `/webhook` endpoint
2. **Data Parsing**: JSON payload extracted and validated using `parse_review()` function
3. **Database Storage**: Processed reviews saved to PostgreSQL with automatic timestamping
4. **Real-time Broadcasting**: New reviews trigger WebSocket events to connected clients
5. **UI Updates**: Frontend receives notifications and triggers page refresh with visual celebration

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and connection management
- **Flask-SocketIO**: WebSocket support for real-time features
- **psycopg2**: PostgreSQL database adapter
- **pytz**: Timezone handling for display formatting

### Frontend Libraries
- **Socket.IO Client**: Real-time communication with backend
- **Canvas-Confetti**: Animation library for user engagement

## Deployment Strategy

### Environment Configuration
- **DATABASE_URL**: PostgreSQL connection string (required)
- **FLASK_SECRET_KEY**: Session security key with fallback for development
- **Database Auto-initialization**: Tables created automatically on startup

### Production Setup
- **WSGI Server**: Gunicorn with Eventlet workers for async WebSocket support
- **Connection Resilience**: Database connection pooling with ping checks and recycling
- **Error Recovery**: Graceful handling of database disconnections and reconnections

### Data Management
- **Automatic Cleanup**: System maintains only 100 most recent reviews for optimal performance
- **Error Handling**: Comprehensive exception handling with user-friendly error pages
- **Logging**: Debug-level logging for development and troubleshooting

The application follows a clean separation of concerns with modular components, making it easy to extend with additional features like advanced analytics, multi-store support, or enhanced filtering capabilities.