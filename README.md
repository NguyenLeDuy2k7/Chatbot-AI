# AI Chatbot with LM Studio Integration

A Flask-based web application that provides a chat interface for interacting with AI models through LM Studio. Features conversation management, persistent chat history, and a modern web interface.

## Features

- **AI Chat Interface**: Interactive chat with AI models via LM Studio
- **Conversation Management**: Create, rename, and delete conversations
- **Persistent History**: SQLite database stores all chat history
- **Modern UI**: Dark theme with responsive design
- **Environment Configuration**: Configurable via environment variables

## Prerequisites

- Python 3.7 or higher
- [LM Studio](https://lmstudio.ai/) installed and running
- A compatible AI model loaded in LM Studio

## Installation

1. **Clone or download the project**
   ```bash
   cd "d:\Code\AI project\AIsite"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database** (automatic on first run)
   - The application will automatically create `chatbot.db` and initialize the schema on first startup

## Configuration

### Environment Variables (Optional)

You can configure the application using environment variables:

- `LM_STUDIO_URL`: LM Studio API endpoint (default: `http://localhost:1234/v1/chat/completions`)
- `DEBUG`: Enable Flask debug mode (default: `False`)

### LM Studio Setup

1. **Install and start LM Studio**
2. **Load a model** in LM Studio
3. **Enable the API server** in LM Studio settings
4. **Update the model name** in `main.py`:
   ```python
   MODEL_NAME = "your-actual-model-name"  # Replace with your model name
   ```

## Usage

### Starting the Application

1. **Make sure LM Studio is running** with a model loaded and API server enabled

2. **Run the Flask application**
   ```bash
   python main.py
   ```

3. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Using the Chat Interface

- **New Conversation**: Click the "New Chat" button in the sidebar
- **Send Messages**: Type your message and press Enter or click Send
- **Manage Conversations**: 
  - Click the "..." menu next to any conversation to rename or delete it
  - Switch between conversations by clicking on them in the sidebar
- **Conversation History**: All conversations are automatically saved and persist between sessions

## File Structure

```
AIsite/
├── main.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── schema.sql          # Database schema
├── chatbot.db          # SQLite database (created automatically)
├── templates/
│   └── index.html      # Main web interface
└── README.md           # This file
```

## API Endpoints

The application exposes several REST API endpoints:

- `GET /` - Main chat interface
- `POST /chat` - Send chat messages
- `GET /history` - Get list of all conversations
- `GET /history/<id>` - Get specific conversation history
- `POST /history/rename/<id>` - Rename a conversation
- `DELETE /history/delete/<id>` - Delete a conversation
- `POST /history/new` - Create new conversation

## Database Schema

The application uses SQLite with the following table:

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    messages TEXT NOT NULL
);
```

## Troubleshooting

### Common Issues

1. **"Failed to get response from AI model"**
   - Ensure LM Studio is running
   - Check that a model is loaded in LM Studio
   - Verify the API server is enabled in LM Studio
   - Check the `LM_STUDIO_URL` configuration

2. **Database errors**
   - Ensure the application has write permissions in the directory
   - Delete `chatbot.db` to reset the database (will lose all chat history)

3. **Port already in use**
   - Change the port in `main.py` by modifying: `app.run(debug=DEBUG, host='0.0.0.0', port=5001)`

### Logs

The application prints helpful information to the console:
- Database initialization status
- LM Studio connection details
- Debug mode status
- Any errors that occur

## Customization

### Changing the System Prompt

Edit the `SYSTEM_PROMPT` variable in `main.py`:
```python
SYSTEM_PROMPT = "You are a helpful AI assistant specialized in..."
```

### Styling

The UI can be customized by editing the CSS in `templates/index.html`.

### Adding Features

The Flask application is modular and can be extended with additional routes and functionality.

## Security Notes

- This application is intended for local development use
- The server binds to `0.0.0.0` by default - be cautious when running on networks
- No authentication is implemented - consider adding auth for production use

## License

This project is open source. Feel free to modify and distribute as needed.