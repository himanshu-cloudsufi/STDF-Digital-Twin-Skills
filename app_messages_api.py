"""
Demand Forecasting Chatbot Server - Messages API Version
Uses Anthropic Messages API with Skills integration via container and code execution
"""

import os
import sys
import asyncio
import argparse
import json
from pathlib import Path
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic
import logging
from database import SessionDatabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = SessionDatabase()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize SocketIO with threading mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Anthropic client (shared across all sessions)
anthropic_client = anthropic.Anthropic()

# Load system prompt from external file
def load_system_prompt():
    """Load system prompt from external file."""
    prompt_path = Path(__file__).parent / 'system_prompt.txt'
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"System prompt file not found at {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        raise

SYSTEM_PROMPT = load_system_prompt()

# Session storage (in-memory for demo - use Redis/DB for production)
# Stores conversation message arrays per session
session_conversations = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_messages_from_history(session_id):
    """
    Build messages array from database conversation history.

    Args:
        session_id: Session identifier

    Returns:
        List of message dictionaries with role and content
    """
    messages = []

    if session_id:
        logger.info(f"[DATA] Building messages from history for session: {session_id}")
        history = db.get_session_history(session_id)
        logger.info(f"[DATA] Retrieved {len(history)} messages from database")

        for i, msg in enumerate(history):
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
            logger.debug(f"[DATA] Message {i+1}: role={msg['role']}, length={len(msg['content'])} chars")

        logger.info(f"[DATA] Built messages array with {len(messages)} items")
    else:
        logger.info("[DATA] No session_id provided, returning empty messages array")

    return messages


def build_container_with_skills():
    """
    Build container configuration with demand forecasting skill.

    Returns:
        Dictionary containing skills configuration for container parameter
    """
    return {
        "skills": [
            {
                "type": "custom",
                "skill_id": "skill_01TipNr17oMetpLYXhSWnjb7",  # demand-forecasting
                "version": "latest"
            },
            {
                "type": "custom",
                "skill_id": "skill_012PamxfW2Gygfu1P6N452WC",  # energy-forecasting
                "version": "latest"
            }
        ]
    }


def get_model_identifier(model_input):
    """
    Map friendly model names to API model identifiers.

    Args:
        model_input: User-friendly model name or full identifier

    Returns:
        API model identifier string
    """
    model_mapping = {
        # Haiku 4.5 (fastest with near-frontier intelligence)
        'claude-haiku-4-5': 'claude-haiku-4-5-20251001',
        'haiku': 'claude-haiku-4-5-20251001',

        # Sonnet 4.5 (best balance of intelligence, speed, and cost)
        'claude-sonnet-4-5': 'claude-sonnet-4-5-20250929',
        'sonnet': 'claude-sonnet-4-5-20250929',
    }
    return model_mapping.get(model_input, model_input)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Serve the chat interface"""
    return send_from_directory('static', 'index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    import datetime
    logger.info("=" * 80)
    logger.info(f"[CONNECTION] Client connected at {datetime.datetime.now()}")
    logger.info(f"[CONNECTION] Active sessions in memory: {len(session_conversations)}")
    logger.info("=" * 80)
    emit('status', {'message': 'Connected to forecasting chatbot'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")


@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages from client"""
    logger.info(f"[INCOMING] Raw data received: {data}")

    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    # Auto-create session if none provided
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        logger.info(f"[SESSION] Auto-created new session: {session_id}")

    logger.info(f"[INCOMING] Received message from client")
    logger.info(f"[INCOMING] Message length: {len(user_message)} chars")
    logger.info(f"[INCOMING] Message preview: {user_message[:100]}...")
    logger.info(f"[INCOMING] Session ID: {session_id}")
    logger.info(f"[INCOMING] Session exists in memory: {session_id in session_conversations if session_id else False}")

    if not user_message:
        logger.warning("[INCOMING] Empty message received, sending error")
        emit('error', {'message': 'Empty message received'})
        return

    # Echo user message back to client WITH session_id
    logger.info("[OUTGOING] Emitting user_message to client")
    emit('user_message', {'message': user_message, 'session_id': session_id})

    # Save user message to database
    try:
        db.save_session(session_id)
        db.save_message(session_id, 'user', user_message)
        logger.info(f"[DATABASE] User message saved for session {session_id}")

        # Log current session size
        history = db.get_session_history(session_id)
        logger.info(f"[DATABASE] Total messages in session: {len(history)}")
    except Exception as e:
        logger.error(f"[DATABASE ERROR] Failed to save user message: {e}", exc_info=True)

    # Process message asynchronously
    logger.info("[PROCESSING] Starting background task for query processing")
    socketio.start_background_task(process_query, user_message, session_id)


def process_query(user_message, session_id=None):
    """
    Process user query using Messages API with Skills integration.

    Args:
        user_message: The user's input message
        session_id: Optional session identifier for conversation continuity
    """
    logger.info("=" * 80)
    logger.info("[AGENT] Starting process_query")
    logger.info(f"[AGENT] Query preview: {user_message[:200]}...")
    logger.info(f"[AGENT] Query length: {len(user_message)} chars")
    logger.info(f"[AGENT] Session ID: {session_id}")
    logger.info("=" * 80)

    try:
        # Build messages array from session history
        if session_id and session_id in session_conversations:
            logger.info(f"[AGENT] Reusing conversation history from MEMORY for session: {session_id}")
            messages = session_conversations[session_id].copy()
            logger.info(f"[AGENT] Loaded {len(messages)} messages from memory")
        else:
            logger.info("[AGENT] Loading conversation history from DATABASE")
            messages = build_messages_from_history(session_id)
            logger.info(f"[AGENT] Loaded {len(messages)} messages from database")

        # Log message history structure
        logger.info(f"[AGENT] Message history breakdown:")
        user_count = sum(1 for m in messages if m.get('role') == 'user')
        assistant_count = sum(1 for m in messages if m.get('role') == 'assistant')
        logger.info(f"[AGENT]   - User messages: {user_count}")
        logger.info(f"[AGENT]   - Assistant messages: {assistant_count}")
        logger.info(f"[AGENT]   - Total messages before new message: {len(messages)}")

        # Append new user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        logger.info(f"[AGENT] Added new user message. Total messages now: {len(messages)}")

        # Get model configuration
        model_input = os.getenv('MODEL', 'claude-sonnet-4-5-20250929')
        model = get_model_identifier(model_input)
        logger.info(f"[AGENT] Using model: {model}")

        # Build container with skills
        container = build_container_with_skills()
        logger.info(f"[AGENT] Container configured with {len(container['skills'])} skills")
        logger.info(f"[AGENT] Skills: {[s['skill_id'] for s in container['skills']]}")

        # Run streaming query
        logger.info("[AGENT] Running streaming query...")
        logger.info(f"[AGENT] Request parameters:")
        logger.info(f"[AGENT]   - Model: {model}")
        logger.info(f"[AGENT]   - Max tokens: 4096")
        logger.info(f"[AGENT]   - Messages count: {len(messages)}")
        logger.info(f"[AGENT]   - System prompt length: {len(SYSTEM_PROMPT)} chars")

        stream_response_sync(anthropic_client, messages, container, model, session_id)
        logger.info("[AGENT] Query completed successfully")

    except Exception as e:
        logger.error(f"[AGENT ERROR] Error processing query: {str(e)}", exc_info=True)
        logger.error(f"[AGENT ERROR] Session ID: {session_id}")
        logger.error(f"[AGENT ERROR] Message count: {len(messages) if 'messages' in locals() else 'N/A'}")
        socketio.emit('error', {'message': f'Error: {str(e)}'})


def stream_response_sync(client, messages, container, model, session_id):
    """
    Stream responses from Messages API to the client using SSE.
    Includes retry logic for handling API overload errors.

    Args:
        client: Anthropic client instance
        messages: Full conversation message array
        container: Container configuration with skills
        model: Model identifier
        session_id: Session identifier for storage
    """
    logger.info("=" * 80)
    logger.info("[STREAM] Starting stream_response")
    logger.info(f"[STREAM] Session ID: {session_id}")
    logger.info(f"[STREAM] Messages to send: {len(messages)}")
    logger.info("=" * 80)

    accumulated_text = ""
    final_message = None
    chunk_count = 0
    start_time = None

    # Retry configuration
    max_retries = 3
    retry_count = 0

    while retry_count <= max_retries:
        try:
            # Create streaming request with stream=True
            logger.info("[STREAM] Creating streaming request to Messages API")
            if retry_count > 0:
                logger.info(f"[STREAM] Retry attempt {retry_count}/{max_retries}")
            logger.info(f"[STREAM] API call parameters:")
            logger.info(f"[STREAM]   - model: {model}")
            logger.info(f"[STREAM]   - max_tokens: 4096")
            logger.info(f"[STREAM]   - messages: {len(messages)} items")
            logger.info(f"[STREAM]   - system prompt: {len(SYSTEM_PROMPT)} chars")
            logger.info(f"[STREAM]   - container skills: {len(container['skills'])}")

            import time
            start_time = time.time()

            with client.beta.messages.stream(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
                container=container,
                tools=[{
                    "type": "code_execution_20250825",
                    "name": "code_execution"
                }],
                betas=["code-execution-2025-08-25", "skills-2025-10-02"]
            ) as stream:
                logger.info("[STREAM] Stream opened, receiving events...")

                # Stream text as it arrives
                for text in stream.text_stream:
                    chunk_count += 1
                    accumulated_text += text

                    if chunk_count % 10 == 0:  # Log every 10th chunk to reduce noise
                        logger.info(f"[STREAM] Chunk #{chunk_count}: {len(text)} chars (total: {len(accumulated_text)})")

                    # Stream text chunk to client
                    socketio.emit('assistant_chunk', {
                        'text': text,
                        'session_id': session_id
                    })

                # Get final message after stream completes
                final_message = stream.get_final_message()
                elapsed = time.time() - start_time
                logger.info(f"[STREAM] Stream completed successfully")
                logger.info(f"[STREAM] Statistics:")
                logger.info(f"[STREAM]   - Total chunks: {chunk_count}")
                logger.info(f"[STREAM]   - Total chars: {len(accumulated_text)}")
                logger.info(f"[STREAM]   - Elapsed time: {elapsed:.2f}s")
                logger.info(f"[STREAM]   - Final message type: {type(final_message)}")
                logger.info(f"[STREAM]   - Final message content blocks: {len(final_message.content) if hasattr(final_message, 'content') else 'N/A'}")

            # Store conversation in memory
            if session_id:
                logger.info(f"[MEMORY] Storing conversation for session {session_id}")

                # Add assistant response to messages
                messages.append({
                    "role": "assistant",
                    "content": final_message.content
                })
                session_conversations[session_id] = messages
                logger.info(f"[MEMORY] Updated session. Total messages: {len(messages)}")

                # Save to database
                try:
                    db.save_message(session_id, 'assistant', accumulated_text)
                    logger.info(f"[DATABASE] Assistant response saved for session {session_id}")
                    logger.info(f"[DATABASE] Saved {len(accumulated_text)} chars")

                    # Verify save
                    history = db.get_session_history(session_id)
                    logger.info(f"[DATABASE] Verified - Total messages in DB: {len(history)}")
                except Exception as db_error:
                    logger.error(f"[DATABASE ERROR] Failed to save assistant response: {db_error}", exc_info=True)

            # Send completion signal
            logger.info("[OUTGOING] Emitting assistant_complete to client")
            socketio.emit('assistant_complete', {
                'full_text': accumulated_text,
                'session_id': session_id
            })
            logger.info("[OUTGOING] Completion signal sent")

            # Success - break out of retry loop
            break

        except anthropic.APIStatusError as e:
            # Check if it's an overload error
            error_str = str(e)
            is_overload = 'overloaded' in error_str.lower() or (hasattr(e, 'status_code') and e.status_code == 529)

            if is_overload and retry_count < max_retries:
                retry_count += 1
                wait_time = 2 ** (retry_count - 1)  # Exponential backoff: 1s, 2s, 4s
                logger.warning("=" * 80)
                logger.warning(f"[RETRY] API overloaded error detected")
                logger.warning(f"[RETRY] Attempt {retry_count}/{max_retries}")
                logger.warning(f"[RETRY] Waiting {wait_time}s before retry...")
                logger.warning("=" * 80)

                # Notify client about retry
                socketio.emit('retry_notification', {
                    'message': f'API temporarily overloaded. Retrying in {wait_time}s... (Attempt {retry_count}/{max_retries})',
                    'retry_count': retry_count,
                    'max_retries': max_retries,
                    'wait_time': wait_time
                })

                import time
                time.sleep(wait_time)
                continue  # Retry the request
            else:
                # Max retries exceeded or different error type
                logger.error("=" * 80)
                logger.error(f"[STREAM ERROR] API Status Error")
                logger.error(f"[STREAM ERROR] Exception type: {type(e).__name__}")
                logger.error(f"[STREAM ERROR] Exception message: {str(e)}")
                logger.error(f"[STREAM ERROR] Status code: {e.status_code if hasattr(e, 'status_code') else 'N/A'}")
                logger.error(f"[STREAM ERROR] Session ID: {session_id}")
                logger.error(f"[STREAM ERROR] Chunks received before error: {chunk_count}")
                logger.error(f"[STREAM ERROR] Text accumulated: {len(accumulated_text)} chars")
                if retry_count >= max_retries:
                    logger.error(f"[STREAM ERROR] Max retries ({max_retries}) exceeded")
                logger.error("=" * 80, exc_info=True)
                socketio.emit('error', {'message': f'API error after {retry_count} retries: {str(e)}'})
                break

        except Exception as e:
            # Non-API errors - don't retry
            logger.error("=" * 80)
            logger.error(f"[STREAM ERROR] Error in stream response")
            logger.error(f"[STREAM ERROR] Exception type: {type(e).__name__}")
            logger.error(f"[STREAM ERROR] Exception message: {str(e)}")
            logger.error(f"[STREAM ERROR] Session ID: {session_id}")
            logger.error(f"[STREAM ERROR] Chunks received before error: {chunk_count}")
            logger.error(f"[STREAM ERROR] Text accumulated: {len(accumulated_text)} chars")
            logger.error("=" * 80, exc_info=True)
            socketio.emit('error', {'message': f'Stream error: {str(e)}'})
            break


@socketio.on('clear_session')
def handle_clear_session(data):
    """Clear the current session"""
    session_id = data.get('session_id')
    if session_id and session_id in session_conversations:
        logger.info(f"Clearing session: {session_id}")
        del session_conversations[session_id]
        emit('status', {'message': 'Session cleared'})
    else:
        logger.info(f"Session not found: {session_id}")
        emit('status', {'message': 'No active session to clear'})


@socketio.on('list_sessions')
def handle_list_sessions():
    """List all saved sessions"""
    try:
        logger.info("[SESSION] Listing all sessions")
        sessions = db.list_sessions(limit=100)
        emit('sessions_list', {'sessions': sessions})
        logger.info(f"[SESSION] Sent {len(sessions)} sessions to client")
    except Exception as e:
        logger.error(f"[SESSION ERROR] Error listing sessions: {e}")
        emit('error', {'message': 'Failed to load session history'})


@socketio.on('resume_session')
def handle_resume_session(data):
    """Resume a previously saved session"""
    session_id = data.get('session_id')

    logger.info("=" * 80)
    logger.info(f"[SESSION] Resume request for session: {session_id}")

    if not session_id:
        logger.warning("[SESSION] No session ID provided")
        emit('error', {'message': 'Session ID required'})
        return

    try:
        # Get session from database
        session_info = db.get_session(session_id)
        if not session_info:
            logger.warning(f"[SESSION] Session not found in database: {session_id}")
            emit('error', {'message': 'Session not found'})
            return

        logger.info(f"[SESSION] Found session in database")
        logger.info(f"[SESSION] Session info: {session_info}")

        # Get conversation history
        history = db.get_session_history(session_id)
        logger.info(f"[SESSION] Retrieved {len(history)} messages from database")

        # Build messages array from history
        messages = build_messages_from_history(session_id)
        logger.info(f"[SESSION] Built messages array with {len(messages)} items")

        # Log message breakdown
        user_msgs = sum(1 for m in messages if m.get('role') == 'user')
        assistant_msgs = sum(1 for m in messages if m.get('role') == 'assistant')
        logger.info(f"[SESSION] Message breakdown: {user_msgs} user, {assistant_msgs} assistant")

        # Store in session conversations
        session_conversations[session_id] = messages
        logger.info(f"[SESSION] Stored in memory. Total active sessions: {len(session_conversations)}")

        # Send session info and history to client
        emit('session_resumed', {
            'session_id': session_id,
            'session_info': session_info,
            'history': history
        })

        logger.info(f"[SESSION] Session {session_id} resumed successfully")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[SESSION ERROR] Error resuming session {session_id}")
        logger.error(f"[SESSION ERROR] Exception: {str(e)}")
        logger.error("=" * 80, exc_info=True)
        emit('error', {'message': f'Failed to resume session: {str(e)}'})


@socketio.on('delete_session')
def handle_delete_session(data):
    """Delete a session from the database"""
    session_id = data.get('session_id')

    if not session_id:
        emit('error', {'message': 'Session ID required'})
        return

    try:
        logger.info(f"[SESSION] Deleting session: {session_id}")

        # Remove from active sessions if present
        if session_id in session_conversations:
            del session_conversations[session_id]

        # Delete from database
        success = db.delete_session(session_id)

        if success:
            emit('session_deleted', {'session_id': session_id})
            logger.info(f"[SESSION] Session {session_id} deleted successfully")
        else:
            emit('error', {'message': 'Session not found'})

    except Exception as e:
        logger.error(f"[SESSION ERROR] Error deleting session {session_id}: {e}")
        emit('error', {'message': f'Failed to delete session: {str(e)}'})


@socketio.on('update_session_title')
def handle_update_session_title(data):
    """Update the title of a session"""
    session_id = data.get('session_id')
    new_title = data.get('title', '').strip()

    if not session_id or not new_title:
        emit('error', {'message': 'Session ID and title required'})
        return

    try:
        logger.info(f"[SESSION] Updating title for session {session_id}: {new_title}")

        success = db.update_session_title(session_id, new_title)

        if success:
            emit('session_title_updated', {
                'session_id': session_id,
                'title': new_title
            })
            logger.info(f"[SESSION] Title updated successfully")
        else:
            emit('error', {'message': 'Session not found'})

    except Exception as e:
        logger.error(f"[SESSION ERROR] Error updating session title: {e}")
        emit('error', {'message': f'Failed to update title: {str(e)}'})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Demand Forecasting Chatbot Server')
    parser.add_argument('--model', type=str,
                       help='Claude model to use (default: claude-sonnet-4-5, options: claude-haiku-4-5 or haiku, claude-sonnet-4-5 or sonnet)')
    parser.add_argument('--port', type=int,
                       help='Port to run server on (default: 8000)')
    args = parser.parse_args()

    # Override environment variables with command line arguments if provided
    if args.model:
        os.environ['MODEL'] = args.model
    if args.port:
        os.environ['PORT'] = str(args.port)

    # Ensure API key is set
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.error("ANTHROPIC_API_KEY not found in environment variables!")
        logger.error("Please create a .env file with your API key")
        exit(1)

    # Verify static directory exists
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)

    # Get configuration
    port = int(os.getenv('PORT', 8000))
    model = os.getenv('MODEL', 'claude-sonnet-4-5')

    # Log startup information
    logger.info("=" * 80)
    logger.info("Starting Demand Forecasting Chatbot Server (Messages API)")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Model: {model} (mapped to: {get_model_identifier(model)})")
    logger.info(f"  - Port: {port}")
    logger.info(f"  - URL: http://localhost:{port}")
    logger.info(f"  - Database: sessions.db")
    logger.info(f"  - Static folder: {static_dir}")
    logger.info(f"  - API Key: {'✓ Set' if os.getenv('ANTHROPIC_API_KEY') else '✗ Missing'}")
    logger.info(f"  - Debug mode: True")
    logger.info(f"  - Async mode: threading")
    logger.info("=" * 80)
    logger.info("Skills Configuration:")
    container = build_container_with_skills()
    for skill in container['skills']:
        logger.info(f"  - {skill['skill_id']} (version: {skill['version']})")
    logger.info("=" * 80)
    logger.info("Server starting...")
    logger.info("=" * 80)

    # Run with threading mode
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
