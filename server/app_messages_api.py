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
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic
import logging
from database import SessionDatabase

# Load environment variables from server directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = SessionDatabase()

# Initialize Flask app (API only, no static files)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO with threading mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Anthropic client (shared across all sessions)
anthropic_client = anthropic.Anthropic()

# Load system prompt from external file
def load_system_prompt():
    """Load system prompt from external file."""
    prompt_path = Path(__file__).parent / 'prompts' / 'system_prompt.txt'
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
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'Demand Forecasting Chatbot API'}, 200


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

    user_message = data.get('content', '').strip()  # Changed from 'message' to 'content'
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

                # Track content blocks for proper handling
                content_blocks = {}  # index -> {type, accumulated_data}

                # Process all events from the stream
                for event in stream:
                    chunk_count += 1

                    if chunk_count % 20 == 0:  # Log every 20th event to reduce noise
                        logger.info(f"[STREAM] Event #{chunk_count}: {event.type}")

                    # Handle different event types
                    if event.type == "content_block_start":
                        block_index = event.index
                        block_type = event.content_block.type

                        logger.info(f"[STREAM] Content block #{block_index} started: {block_type}")

                        # Initialize block tracking
                        content_blocks[block_index] = {
                            'type': block_type,
                            'accumulated_text': '',
                            'accumulated_json': '',
                            'tool_name': getattr(event.content_block, 'name', None),
                            'tool_id': getattr(event.content_block, 'id', None)
                        }

                        # Emit block start event to frontend
                        socketio.emit('content_block_start', {
                            'type': block_type,
                            'id': content_blocks[block_index]['tool_id'] or f"block_{block_index}",
                            'name': content_blocks[block_index]['tool_name']
                        })

                    elif event.type == "content_block_delta":
                        block_index = event.index
                        delta = event.delta

                        if block_index not in content_blocks:
                            logger.warning(f"[STREAM] Received delta for unknown block index {block_index}")
                            continue

                        block_info = content_blocks[block_index]

                        # Handle text delta
                        if delta.type == "text_delta":
                            text = delta.text
                            block_info['accumulated_text'] += text
                            accumulated_text += text

                            # Stream text chunk to client (existing behavior)
                            socketio.emit('assistant_chunk', {
                                'content': text,
                                'session_id': session_id
                            })

                        # Handle input JSON delta (tool parameters)
                        elif delta.type == "input_json_delta":
                            json_chunk = delta.partial_json
                            block_info['accumulated_json'] += json_chunk

                            logger.info(f"[STREAM] Tool input delta: {json_chunk}")

                            # Emit tool input delta to frontend
                            socketio.emit('tool_input_delta', {
                                'id': block_info['tool_id'] or f"block_{block_index}",
                                'input': json_chunk
                            })

                        # Handle thinking delta
                        elif delta.type == "thinking_delta":
                            thinking_text = delta.thinking
                            block_info['accumulated_text'] += thinking_text

                            logger.info(f"[STREAM] Thinking delta: {thinking_text[:100]}...")

                            # Emit thinking chunk to frontend
                            socketio.emit('thinking_chunk', {
                                'id': block_info['tool_id'] or f"block_{block_index}",
                                'content': thinking_text
                            })

                    elif event.type == "content_block_stop":
                        block_index = event.index

                        if block_index in content_blocks:
                            block_info = content_blocks[block_index]
                            logger.info(f"[STREAM] Content block #{block_index} stopped: {block_info['type']}")

                            # Emit block stop event to frontend
                            socketio.emit('content_block_stop', {
                                'id': block_info['tool_id'] or f"block_{block_index}"
                            })

                    elif event.type == "message_start":
                        logger.info(f"[STREAM] Message started: {event.message.id}")

                        # Emit message start with metadata
                        socketio.emit('message_start', {
                            'message_id': event.message.id,
                            'model': event.message.model,
                            'session_id': session_id
                        })

                    elif event.type == "message_delta":
                        logger.info(f"[STREAM] Message delta: stop_reason={event.delta.stop_reason}")

                        # Emit usage statistics if available
                        if hasattr(event, 'usage'):
                            socketio.emit('usage_update', {
                                'usage': {
                                    'input_tokens': getattr(event.usage, 'input_tokens', 0),
                                    'output_tokens': getattr(event.usage, 'output_tokens', 0)
                                },
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

                    # Auto-generate title after 3rd assistant response
                    assistant_count = sum(1 for msg in history if msg.get('role') == 'assistant')
                    logger.info(f"[TITLE GEN] Assistant message count: {assistant_count}")

                    if assistant_count == 3:
                        logger.info("[TITLE GEN] 3rd assistant response detected - triggering auto-naming")

                        # Get user messages only
                        user_messages = [msg['content'] for msg in history if msg.get('role') == 'user']
                        logger.info(f"[TITLE GEN] Extracted {len(user_messages)} user messages")

                        # Generate title with Haiku
                        generated_title = generate_chat_title_with_haiku(user_messages)

                        if generated_title:
                            # Update database
                            success = db.update_session_title(session_id, generated_title)

                            if success:
                                logger.info(f"[TITLE GEN] Title auto-generated and saved: '{generated_title}'")

                                # Notify frontend
                                socketio.emit('session_renamed', {
                                    'session_id': session_id,
                                    'title': generated_title
                                })
                                logger.info("[TITLE GEN] Frontend notified of new title")
                            else:
                                logger.warning("[TITLE GEN] Failed to save generated title to database")
                        else:
                            logger.warning("[TITLE GEN] Title generation returned None")

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
            'messages': history
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
            emit('session_renamed', {
                'session_id': session_id,
                'title': new_title
            })
            logger.info(f"[SESSION] Title updated successfully")
        else:
            emit('error', {'message': 'Session not found'})

    except Exception as e:
        logger.error(f"[SESSION ERROR] Error updating session title: {e}")
        emit('error', {'message': f'Failed to update title: {str(e)}'})


@socketio.on('backfill_session_titles')
def handle_backfill_session_titles():
    """
    Backfill titles for existing sessions that have 3+ messages but no custom title.
    Generates titles using Haiku for all qualifying sessions.
    """
    logger.info("=" * 80)
    logger.info("[BACKFILL] Starting title backfill for existing sessions")

    try:
        # Get all sessions that need titles
        # We look for sessions with at least 6 messages (3 user + 3 assistant)
        # and either no title or default title pattern "Chat <session_id>"
        sessions_to_update = db.get_sessions_needing_titles()

        logger.info(f"[BACKFILL] Found {len(sessions_to_update)} sessions needing titles")

        if not sessions_to_update:
            emit('backfill_complete', {
                'updated_count': 0,
                'message': 'No sessions need title backfill'
            })
            return

        updated_count = 0
        failed_count = 0

        for session in sessions_to_update:
            session_id = session['session_id']
            logger.info(f"[BACKFILL] Processing session {session_id}")

            try:
                # Get session history
                history = db.get_session_history(session_id)

                # Extract user messages only
                user_messages = [msg['content'] for msg in history if msg.get('role') == 'user'][:3]

                if len(user_messages) < 1:
                    logger.warning(f"[BACKFILL] Skipping {session_id} - no user messages found")
                    failed_count += 1
                    continue

                logger.info(f"[BACKFILL] Generating title for {session_id} using {len(user_messages)} user messages")

                # Generate title
                generated_title = generate_chat_title_with_haiku(user_messages)

                if generated_title:
                    # Update database
                    success = db.update_session_title(session_id, generated_title)

                    if success:
                        updated_count += 1
                        logger.info(f"[BACKFILL] Updated {session_id}: '{generated_title}'")
                    else:
                        failed_count += 1
                        logger.warning(f"[BACKFILL] Failed to save title for {session_id}")
                else:
                    failed_count += 1
                    logger.warning(f"[BACKFILL] Title generation failed for {session_id}")

            except Exception as session_error:
                failed_count += 1
                logger.error(f"[BACKFILL ERROR] Error processing session {session_id}: {session_error}")
                continue

        # Send completion notification
        logger.info("=" * 80)
        logger.info(f"[BACKFILL] Complete: {updated_count} updated, {failed_count} failed")
        logger.info("=" * 80)

        emit('backfill_complete', {
            'updated_count': updated_count,
            'failed_count': failed_count,
            'total_processed': len(sessions_to_update),
            'message': f'Backfill complete: {updated_count} sessions updated, {failed_count} failed'
        })

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[BACKFILL ERROR] Error during backfill: {e}")
        logger.error("=" * 80, exc_info=True)
        emit('error', {'message': f'Backfill failed: {str(e)}'})


@socketio.on('compare_sessions')
def handle_compare_sessions(data):
    """Compare two chat sessions using Haiku model to find numerical discrepancies"""
    session_id_1 = data.get('session_id_1')
    session_id_2 = data.get('session_id_2')

    logger.info("=" * 80)
    logger.info(f"[COMPARE] Compare request for sessions: {session_id_1} and {session_id_2}")

    if not session_id_1 or not session_id_2:
        logger.warning("[COMPARE] Missing session IDs")
        emit('error', {'message': 'Two session IDs required for comparison'})
        return

    if session_id_1 == session_id_2:
        logger.warning("[COMPARE] Same session ID provided twice")
        emit('error', {'message': 'Cannot compare a session with itself'})
        return

    try:
        # Get both session info and history
        session_1_info = db.get_session(session_id_1)
        session_2_info = db.get_session(session_id_2)

        if not session_1_info or not session_2_info:
            logger.warning("[COMPARE] One or both sessions not found")
            emit('error', {'message': 'One or both sessions not found'})
            return

        history_1 = db.get_session_history(session_id_1)
        history_2 = db.get_session_history(session_id_2)

        logger.info(f"[COMPARE] Session 1: {len(history_1)} messages")
        logger.info(f"[COMPARE] Session 2: {len(history_2)} messages")

        # Format transcripts
        transcript_1 = format_transcript(history_1)
        transcript_2 = format_transcript(history_2)

        # Call Haiku for comparison
        logger.info("[COMPARE] Calling Haiku model for analysis...")
        comparison_result = compare_with_haiku(
            transcript_1,
            transcript_2,
            session_1_info.get('title', 'Chat 1'),
            session_2_info.get('title', 'Chat 2')
        )

        logger.info("[COMPARE] Comparison complete")
        logger.info("=" * 80)

        # Emit results
        emit('comparison_complete', {
            'session_1': {
                'id': session_id_1,
                'title': session_1_info.get('title', 'Chat 1'),
                'message_count': len(history_1)
            },
            'session_2': {
                'id': session_id_2,
                'title': session_2_info.get('title', 'Chat 2'),
                'message_count': len(history_2)
            },
            'comparison': comparison_result
        })

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[COMPARE ERROR] Error comparing sessions")
        logger.error(f"[COMPARE ERROR] Exception: {str(e)}")
        logger.error("=" * 80, exc_info=True)
        emit('error', {'message': f'Failed to compare sessions: {str(e)}'})


def format_transcript(history):
    """Format conversation history into readable transcript"""
    lines = []
    for msg in history:
        role = msg['role'].upper()
        content = msg['content']
        timestamp = msg.get('timestamp', '')
        lines.append(f"[{role}]: {content}\n")
    return "\n".join(lines)


def compare_with_haiku(transcript_1, transcript_2, title_1, title_2):
    """
    Use Haiku model to compare two transcripts and identify numerical discrepancies.
    Focuses on forecast/prediction differences.

    Args:
        transcript_1: Full conversation transcript from first session
        transcript_2: Full conversation transcript from second session
        title_1: Title of first session
        title_2: Title of second session

    Returns:
        String containing comparison summary
    """
    logger.info("[HAIKU] Building comparison prompt...")

    # Build comparison prompt
    comparison_prompt = f"""You are analyzing two different chat conversations about forecasting and predictions.

**Chat 1: {title_1}**
{transcript_1}

---

**Chat 2: {title_2}**
{transcript_2}

---

Please analyze these two conversations and identify any significant numerical discrepancies, particularly focusing on:
- Forecast results and predictions
- Key metrics and statistics
- Years, dates, or timeframes
- Percentages, growth rates, or CAGRs
- Capacity, demand, or generation figures
- Cost calculations or tipping points

Provide a **concise summary** of the major differences. For each discrepancy:
1. Describe what the difference is about (the topic/metric)
2. State the value from Chat 1
3. State the value from Chat 2
4. Briefly explain why this difference might be significant

If there are no significant numerical differences, state that clearly.

Keep your response focused and concise - aim for 3-10 bullet points highlighting only the most important discrepancies."""

    logger.info(f"[HAIKU] Prompt length: {len(comparison_prompt)} chars")

    try:
        # Call Haiku model directly (non-streaming for simplicity)
        logger.info("[HAIKU] Making API call to Haiku model...")

        response = anthropic_client.messages.create(
            model=get_model_identifier('haiku'),
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": comparison_prompt
            }]
        )

        # Extract text from response
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text += block.text

        logger.info(f"[HAIKU] Response received: {len(result_text)} chars")

        return result_text

    except Exception as e:
        logger.error(f"[HAIKU ERROR] Error calling Haiku model: {e}", exc_info=True)
        return f"Error during comparison: {str(e)}"


def generate_chat_title_with_haiku(user_messages):
    """
    Generate an action-oriented title for a chat session using Haiku.
    Uses only user messages to create a concise, descriptive title.

    Args:
        user_messages: List of user message strings (first 3 messages recommended)

    Returns:
        String containing generated title (max 60 chars), or None if generation fails
    """
    logger.info("[TITLE GEN] Generating chat title with Haiku...")

    if not user_messages:
        logger.warning("[TITLE GEN] No user messages provided")
        return None

    # Limit to first 3 user messages for context
    messages_to_use = user_messages[:3]

    # Format messages for the prompt
    formatted_messages = "\n\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(messages_to_use)])

    logger.info(f"[TITLE GEN] Using {len(messages_to_use)} user messages")

    # Build title generation prompt
    title_prompt = f"""Based on the following user messages from a forecasting conversation, generate a brief, action-oriented title.

User messages:
{formatted_messages}

Requirements:
- Maximum 60 characters
- Action-oriented format (describe what the user wants to do)
- Examples: "Forecast solar capacity for 2040", "Analyze EV adoption in China", "Compare wind vs coal generation"
- Focus on the main topic and action
- Do NOT include quotes or extra punctuation

Generate only the title text, nothing else:"""

    logger.info(f"[TITLE GEN] Prompt length: {len(title_prompt)} chars")

    try:
        # Call Haiku model (fast and cost-efficient)
        logger.info("[TITLE GEN] Making API call to Haiku model...")

        response = anthropic_client.messages.create(
            model=get_model_identifier('haiku'),
            max_tokens=100,  # Small limit since we only need a short title
            messages=[{
                "role": "user",
                "content": title_prompt
            }]
        )

        # Extract text from response
        title = ""
        for block in response.content:
            if hasattr(block, 'text'):
                title += block.text

        # Clean up title (remove quotes, trim whitespace, limit length)
        title = title.strip().strip('"').strip("'")[:60]

        logger.info(f"[TITLE GEN] Generated title: '{title}'")

        return title

    except Exception as e:
        logger.error(f"[TITLE GEN ERROR] Error generating title: {e}", exc_info=True)
        return None


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

    # Get configuration
    port = int(os.getenv('PORT', 8000))
    model = os.getenv('MODEL', 'claude-sonnet-4-5')

    # Log startup information
    logger.info("=" * 80)
    logger.info("Starting Demand Forecasting Chatbot Server (API/WebSocket Only)")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Mode: API + WebSocket Server (No file serving)")
    logger.info(f"  - Model: {model} (mapped to: {get_model_identifier(model)})")
    logger.info(f"  - Port: {port}")
    logger.info(f"  - WebSocket URL: ws://localhost:{port}")
    logger.info(f"  - Health Check: http://localhost:{port}/")
    logger.info(f"  - Database: sessions.db")
    logger.info(f"  - CORS: Enabled for all origins")
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
    logger.info("Ready for React app connections")
    logger.info("=" * 80)

    # Run with threading mode
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
