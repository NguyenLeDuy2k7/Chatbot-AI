from flask import Flask, render_template, request, jsonify
import requests
import json
import os
import sqlite3

app = Flask(__name__)

# --- Configuration ---
LM_STUDIO_API_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions") # Use environment variable for LM Studio URL
MODEL_NAME = "your-model-name" # Replace with your model name, or also make it an environment variable if needed
SYSTEM_PROMPT = "You are a helpful AI assistant." # Optional system prompt
DEBUG = os.environ.get("DEBUG", "False").lower() == "true" # Use environment variable for debug mode
DATABASE = 'chatbot.db'

# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema if it doesn't exist."""
    with app.app_context():
        db = get_db_connection()
        with open('schema.sql', 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        db.close()
        print("Database initialized.")

def get_conversation_history_db(conversation_id):
    """Fetch conversation history from the database."""
    db = get_db_connection()
    try:
        conversation_data = db.execute("SELECT messages FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        db.close()
        if conversation_data:
            return json.loads(conversation_data['messages'])
        else:
            return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return None

def update_conversation_db(conversation_id, messages):
    """Update the conversation messages in the database."""
    db = get_db_connection()
    try:
        db.execute("UPDATE conversations SET messages = ? WHERE id = ?", (json.dumps(messages), conversation_id)) # Save messages as JSON string
        db.commit()
        db.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return False

def create_conversation_db():
    """Create a new conversation entry in the database and return its ID."""
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("INSERT INTO conversations (name, messages) VALUES (?, ?)", ('New Conversation', json.dumps([]))) # Initial conversation with empty messages
        conversation_id = cursor.lastrowid
        db.commit()
        db.close()
        return conversation_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return None

def get_conversation_list_db():
    """Fetch a list of conversations (IDs and names) from the database."""
    db = get_db_connection()
    try:
        conversations = db.execute("SELECT id, name FROM conversations").fetchall()
        db.close()
        return [{"id": row['id'], "name": row['name']} for row in conversations]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return []

def rename_conversation_db(conversation_id, new_name):
    """Rename a conversation in the database."""
    db = get_db_connection()
    try:
        db.execute("UPDATE conversations SET name = ? WHERE id = ?", (new_name, conversation_id))
        db.commit()
        db.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return False

def delete_conversation_db(conversation_id):
    """Delete a conversation from the database."""
    db = get_db_connection()
    try:
        db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        db.commit()
        db.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.close()
        return False


# --- LM Studio Interaction Function ---
def get_lm_studio_response(messages):
    """Send messages to LM Studio API and get the response."""
    try:
        payload = {
            "messages": messages,
            "model": MODEL_NAME,
            "stream": False # Set to True if you want streaming
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(LM_STUDIO_API_URL, headers=headers, json=payload, timeout=3000) # Timeout for robustness
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()

        if 'choices' in response_json and response_json['choices']:
            reply = response_json['choices'][0]['message']['content']
            return reply.strip()
        else:
            print(f"Unexpected LM Studio response format: {response_json}") # Log unexpected response
            return "Sorry, I couldn't generate a response."

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with LM Studio API: {e}") # Log request errors
        return "Failed to get response from AI model."
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from LM Studio API: {e}, Response text: {response.text if 'response' in locals() else 'No response'}") # Log JSON decode errors
        return "Error processing AI response."


# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the main HTML page, passing conversation history."""
    conversations = get_conversation_list_db()
    return render_template('index.html', conversations=conversations) # Pass conversations to template

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint to handle chatbot messages."""
    data = request.get_json()
    message = data.get('message')
    conversation_id = data.get('conversation_id')

    if not message:
        return jsonify({"error": "Message content is missing."}), 400

    conversation_history = []
    if conversation_id:
        conversation_history = get_conversation_history_db(conversation_id)
        if conversation_history is None:
            return jsonify({"error": "Invalid conversation ID."}), 400

    # Append user message to conversation history
    conversation_history.append({"role": "user", "content": message})


    # Prepare messages for LM Studio API, include system prompt and conversation history
    lm_studio_messages = []
    if SYSTEM_PROMPT:
        lm_studio_messages.append({"role": "system", "content": SYSTEM_PROMPT})
    lm_studio_messages.extend(conversation_history)


    # Get response from LM Studio
    reply_text = get_lm_studio_response(lm_studio_messages)

    # Append bot response to conversation history
    conversation_history.append({"role": "assistant", "content": reply_text})


    if conversation_id:
        update_conversation_db(conversation_id, conversation_history) # Update existing conversation
    else:
        conversation_id = create_conversation_db() # Create new conversation if no ID was provided
        if conversation_id:
            update_conversation_db(conversation_id, conversation_history) # Save initial turn for new conversation
        else:
            return jsonify({"error": "Failed to create new conversation."}), 500

    return jsonify({"reply": reply_text, "conversation_id": conversation_id})


@app.route('/history', methods=['GET'])
def history():
    """API endpoint to get the list of conversations."""
    conversation_list = get_conversation_list_db()
    return jsonify(conversation_list)

@app.route('/history/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """API endpoint to get a specific conversation's history."""
    history = get_conversation_history_db(conversation_id)
    if history is None:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(history)

@app.route('/history/rename/<int:conversation_id>', methods=['POST'])
def rename_conversation(conversation_id):
    """API endpoint to rename a conversation."""
    data = request.get_json()
    new_name = data.get('name')
    if not new_name:
        return jsonify({"error": "New name is required"}), 400
    if rename_conversation_db(conversation_id, new_name):
        return jsonify({"message": "Conversation renamed successfully"})
    else:
        return jsonify({"error": "Conversation not found"}), 404

@app.route('/history/delete/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """API endpoint to delete a conversation."""
    if delete_conversation_db(conversation_id):
        return jsonify({"message": "Conversation deleted successfully"})
    else:
        return jsonify({"error": "Conversation not found"}), 404

@app.route('/history/new', methods=['POST'])
def new_conversation():
    """API endpoint to create a new conversation."""
    conversation_id = create_conversation_db()
    if conversation_id:
        return jsonify({"conversation_id": conversation_id})
    else:
        return jsonify({"error": "Failed to create new conversation."}), 500


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("Database file not found. Initializing database...")
        init_db()
    else:
        print("Database file found.")

    print("Server is starting, make sure LM Studio is running and accessible at", LM_STUDIO_API_URL)
    print("Debug mode is:", DEBUG)

    app.run(debug=DEBUG, host='0.0.0.0')