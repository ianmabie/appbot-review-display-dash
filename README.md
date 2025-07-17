# App Review Webhook Receiver

A comprehensive webhook receiver application designed to capture, parse, and analyze app reviews from multiple external sources. The system provides real-time data collection, advanced filtering, and interactive visualization of review insights.

## Features

- **Real-time Webhook Processing**: Receives and processes app review data from external sources
- **Interactive Dashboard**: Clean, responsive interface for viewing and managing reviews
- **Smart Filtering**: Toggle between all reviews and "Good Vibes Only" mode (5-star reviews)
- **Auto-cleanup**: Maintains only the 100 most recent reviews for optimal performance
- **Live Updates**: Real-time notifications when new reviews arrive with confetti celebration
- **Review Management**: Hide/show individual reviews with persistent state storage
- **Sentiment Analysis**: Captures and displays review sentiment data
- **Multi-store Support**: Handles reviews from different app stores

## Technology Stack

- **Backend**: Python 3.11 with Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Real-time Communication**: Flask-SocketIO for WebSocket connections
- **Frontend**: HTML5, CSS3, JavaScript with Socket.IO client
- **Deployment**: Gunicorn with Eventlet for production

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd webhook-app-review-parser
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/database"
   export FLASK_SECRET_KEY="your-secret-key-here"
   ```

4. **Initialize the database**:
   The application will automatically create the required tables on startup.

## Usage

### Starting the Application

**Development mode**:
```bash
python main.py
```

**Production mode**:
```bash
gunicorn main:app -b 0.0.0.0:5000 -w 1 --worker-class eventlet
```

The application will be available at `http://localhost:5000`

### Webhook Integration

Send POST requests to the `/webhook` endpoint with the following JSON structure:

```json
{
  "reviews": [
    {
      "app_id": 12345,
      "app_store_id": "com.example.app",
      "author": "John Doe",
      "rating": 5,
      "subject": "Great app!",
      "body": "This app is amazing and works perfectly.",
      "published_at": "2025-01-15",
      "sentiment": "positive"
    }
  ]
}
```

### Dashboard Features

- **Main View**: Displays the 100 most recent reviews in a responsive grid layout
- **Filter Toggle**: Switch between viewing all reviews or only 5-star reviews
- **Hide Reviews**: Click the × button on any review card to hide it (state persists)
- **Real-time Updates**: New reviews trigger confetti animation and automatic refresh
- **Auto-hide**: Reviews containing "test" or "appbot" are automatically hidden

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard displaying reviews |
| `/webhook` | POST | Webhook endpoint for receiving review data |

## Database Schema

### Reviews Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| app_id | Integer | Application identifier |
| app_store_id | String(50) | App store identifier |
| author | String(100) | Review author name |
| rating | Integer | Rating (1-5 stars) |
| subject | String(200) | Review subject/title |
| body | Text | Review content |
| published_at | Date | Original publication date |
| sentiment | String(50) | Sentiment analysis result |
| received_at | DateTime | When review was received by webhook |

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (auto-generated if not provided)

### Database Configuration

The application uses connection pooling with the following settings:
- Pool recycle: 300 seconds
- Pool pre-ping: Enabled
- Pool timeout: 20 seconds
- Max overflow: 0

## Development

### Project Structure

```
├── app.py              # Flask application initialization
├── main.py             # Main application with routes and logic
├── models.py           # SQLAlchemy database models
├── templates/
│   ├── index.html      # Main dashboard template
│   └── error.html      # Error page template
├── static/
│   └── styles.css      # Application styling
├── pyproject.toml      # Python dependencies
└── README.md           # This file
```

### Key Components

- **Webhook Parser**: Validates and processes incoming review data
- **Review Model**: SQLAlchemy model for database interactions
- **SocketIO Integration**: Real-time client-server communication
- **Auto-cleanup**: Maintains optimal database size
- **Error Handling**: Comprehensive error handling with logging

## Deployment

The application is designed to run on Replit and includes:
- Gunicorn configuration for production
- Eventlet worker for WebSocket support
- Automatic database initialization
- Health checks and error recovery

## Monitoring

The application includes comprehensive logging:
- Webhook payload logging
- Database operation tracking
- Error monitoring and rollback handling
- Performance metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please refer to the application logs or contact the development team.