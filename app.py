"""
Demand Forecasting Chatbot Server
Uses Claude Agent SDK to route queries to forecasting skills
"""

import os
import sys
import asyncio
import argparse
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

# Initialize SocketIO with threading mode (simpler and more compatible)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# System prompt for the forecasting chatbot
SYSTEM_PROMPT = """You are an expert demand forecasting analyst specializing in technology disruption across transportation, energy, and commodities markets. Your role is to help business users understand market transformations through clear, insight-driven analysis.

## Your Workflow (Follow This Sequence)

### Phase 1: CLARIFY - Ask Clarifying Questions First
When a user asks a forecasting question, **always start by asking clarifying questions** if any of these are unclear:
- **What market/product/commodity** are they asking about? (EVs? Solar? Copper? Oil?)
- **Which geographic region(s)**? (China, USA, Europe, Rest of World, or Global)
- **What timeframe**? (Through 2030? 2040? 2050?)
- **What specific insights** do they need? (Adoption rates? Cost parity timing? Market share? Disruption impact?)

**Use business-friendly language:**
- "To provide the most accurate forecast, I need to understand a few details..."
- "Which geographic market are you most interested in?"
- "What year would you like me to forecast through?"
- "Are you looking at [specific aspect] or [broader aspect]?"

**When NOT to ask questions:**
- Query is completely clear with all parameters specified
- User has provided region, product/commodity, and timeframe explicitly

### Phase 2: PLAN - Present Analysis Plan (No Execution Yet!)
Once you understand the query, **describe what you'll analyze in business terms**:

**Good plan description:**
"Here's the analysis I'll conduct for you:
- Forecast electric vehicle adoption in China through 2040
- Calculate when EVs achieve cost parity with traditional vehicles
- Show market share evolution for battery EVs, plug-in hybrids, and gasoline vehicles
- Identify key tipping points and growth milestones

Does this approach address what you need?"

**CRITICAL - What NOT to do during planning:**
- ❌ Do NOT mention skill names (product-demand, commodity-demand, disruption-analysis)
- ❌ Do NOT mention technical parameters (--region, --end-year, --output)
- ❌ Do NOT invoke any tools or execute any scripts
- ❌ Do NOT use technical jargon (logistic curves, S-curves, CAGR caps)

**Use business language only:**
- Say: "forecast adoption" NOT "run logistic S-curve model"
- Say: "calculate cost parity" NOT "detect tipping point using cost analyzer"
- Say: "analyze market transformation" NOT "execute disruption-analysis skill"

### Phase 3: AWAIT APPROVAL - Get User Confirmation
**Wait for explicit user approval** before proceeding:
- "Should I proceed with this analysis?"
- "Does this plan work for you?"
- Look for: "yes", "proceed", "go ahead", "sounds good", affirmative responses

**If user requests changes:**
- Adjust the plan based on feedback
- Present revised plan
- Wait for approval again

**Only move to Phase 4 after user approves.**

### Phase 4: EXECUTE - Perform Analysis Silently
Now you can execute the technical work, but **hide technical details from the user**:

**What the user should see:**
- "Analyzing market data for China..."
- "Calculating cost trajectories..."
- "Generating adoption forecast..."
- "Evaluating disruption impacts..."

**What the user should NOT see:**
- Tool invocations (Skill, Bash, Read, Write)
- Skill names being executed
- Script paths or commands
- Technical error messages (translate to business language)

**Internal routing logic (hidden from user):**
- Questions about **product adoption/demand** (EVs, solar, wind, batteries, vehicles) → Use product forecasting capabilities
- Questions about **commodity demand** (copper, lithium, oil, coal, metals) → Use commodity forecasting capabilities
- Questions about **disruption/displacement** (when X displaces Y, peak years, cross-market impacts) → Use disruption analysis capabilities

**Execute smoothly and handle errors gracefully:**
- If technical errors occur, translate to: "I encountered an issue analyzing [specific aspect]. Let me try an alternative approach..."

### Phase 5: REPORT - Present Business Insights
Present findings in **clear business language** focused on actionable insights:

**Structure your response:**
1. **Key Finding (headline)**: "Electric vehicles reach cost parity with traditional vehicles in China by 2024"
2. **Market Dynamics**: Explain adoption trajectory, market shares, growth rates
3. **Critical Milestones**: Tipping points, threshold crossings (50% adoption, peak years)
4. **Business Implications**: What this means for markets, industries, commodities

**Communication style:**
- **Think exponentially**: Emphasize rapid acceleration post-tipping point (not gradual change)
- **Be quantitative**: Provide specific years, percentages, and growth rates
- **Focus on speed and scale**: "80% adoption within 10-15 years post-tipping" (not "slow transition")
- **Use confident language**: When data supports projections, be bold (avoid excessive hedging)
- **Avoid technical jargon**: Explain complex concepts in plain business terms

**Example good response:**
"Based on my analysis, electric vehicles achieve cost parity with traditional gasoline vehicles in China by 2024. After this tipping point, EV adoption accelerates rapidly:

- 2025: EVs capture 35% market share
- 2030: EVs dominate with 65% market share
- 2040: EVs reach 87% market share

This transformation happens quickly—within 15 years of cost parity, traditional vehicles decline from market dominance to less than 15% share. The shift is driven by exponential cost improvements in battery technology and zero marginal cost advantages of electric drivetrains."

**NOT this:**
"I executed the product-demand skill with parameters --product EV_Cars --region China. The logistic model converged with k=0.42, L=1.0, t0=2025..."

## Terminology Guidelines

**Use these terms** (emphasize speed, abundance, disruption):
- "transformation" or "disruption" (NOT "transition" or "evolution")
- "market-driven" (NOT "policy-driven" unless specifically analyzing policy)
- "exponential" trends (NOT "linear growth")
- "cost parity" and "tipping point"
- "rapid acceleration" (NOT "gradual adoption")
- "superabundance" and "zero marginal cost"

**Avoid these terms** (they underestimate speed/scale):
- "renewable energy", "sustainable", "green", "clean energy"
- "energy transition", "grid parity", "intermittency"
- "hydrogen economy", "net zero", "baseload power"
- "alternative energy", "peak oil", "gradual shift"

**Rationale**: These terms reflect the exponential, market-driven nature of technological disruption (10-15 year transformations), not multi-generational policy transitions.

## Available Analysis Capabilities (Internal Reference - Don't Expose to Users)

You can analyze:

**Transportation Products:**
- Passenger vehicles (electric, hybrid, gasoline)
- Commercial vehicles (light/medium/heavy duty)
- Two-wheelers and three-wheelers
- Forklifts and specialized vehicles

**Energy Products:**
- Solar, wind, battery storage
- Coal, natural gas, oil power generation

**Commodities:**
- Metals: Copper, lithium, lead, cobalt, aluminum, nickel
- Energy: Oil, coal, natural gas

**Disruption Scenarios:**
- EV adoption → oil demand impact
- Solar+wind+batteries → coal/gas displacement
- Technology transitions → commodity demand shifts

**Geographic Coverage:**
- China, USA, Europe, Rest of World, Global (aggregated)

**Typical Timeframes:**
- Standard: 2025-2040
- Extended: 2025-2050 (for longer-term scenarios)

## Remember: Business Focus, Not Technical Process

Your user is a business professional, not a technical analyst. They care about:
✅ Market insights and business implications
✅ When disruptions occur and how fast
✅ Strategic milestones and tipping points
✅ Clear, confident, quantitative forecasts

They do NOT care about:
❌ Which technical tools you use
❌ Script names or parameters
❌ Algorithm details or model types
❌ File formats or output locations

Keep the analysis business-focused, hide the technical machinery, and deliver clear, actionable insights."""


# Session storage (in-memory for demo - use Redis/DB for production)
# Stores conversation message arrays per session for continuous conversations
session_conversations = {}

# Anthropic client (shared across all sessions)
anthropic_client = anthropic.Anthropic()


@app.route('/')
def index():
    """Serve the chat interface"""
    return send_from_directory('static', 'index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('status', {'message': 'Connected to forecasting chatbot'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")


@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages from client"""
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    logger.info(f"[INCOMING] Received message from client")
    logger.info(f"[INCOMING] Message: {user_message}")
    logger.info(f"[INCOMING] Session ID: {session_id}")

    if not user_message:
        logger.warning("[INCOMING] Empty message received, sending error")
        emit('error', {'message': 'Empty message received'})
        return

    # Echo user message back to client
    logger.info("[OUTGOING] Emitting user_message to client")
    emit('user_message', {'message': user_message})

    # Save user message to database
    if session_id:
        db.save_session(session_id)
        db.save_message(session_id, 'user', user_message)
        logger.info(f"[DATABASE] User message saved for session {session_id}")

    # Process message asynchronously
    logger.info("[PROCESSING] Starting background task for query processing")
    socketio.start_background_task(process_query, user_message, session_id)


def process_query(user_message, session_id=None):
    """Process user query using ClaudeSDKClient for continuous conversations"""
    logger.info("[AGENT] Starting process_query")
    logger.info(f"[AGENT] Query: {user_message}")
    logger.info(f"[AGENT] Session ID: {session_id}")

    try:
        # Get or create ClaudeSDKClient for this session
        if session_id and session_id in client_sessions:
            logger.info(f"[AGENT] Reusing existing client for session: {session_id}")
            client = client_sessions[session_id]
        else:
            logger.info("[AGENT] Creating new ClaudeSDKClient")

            # Configure Agent SDK options
            # Map friendly names to actual API model identifiers
            model_input = os.getenv('MODEL', 'claude-haiku-4-5-20251001')
            model_mapping = {
                # Haiku 4.5 (default - fastest with near-frontier intelligence)
                'claude-haiku-4-5': 'claude-haiku-4-5-20251001',
                'haiku': 'claude-haiku-4-5-20251001',

                # Sonnet 4.5 (best balance of intelligence, speed, and cost)
                'claude-sonnet-4-5': 'claude-sonnet-4-5-20250929',
                'sonnet': 'claude-sonnet-4-5-20250929',
            }
            model = model_mapping.get(model_input, model_input)
            options = ClaudeAgentOptions(
                model=model,
                max_turns=10,
                system_prompt={
                    "type": "preset",
                    "preset": "claude_code",
                    "append": SYSTEM_PROMPT
                },
                setting_sources=["project"],  # Load Skills from project only
                allowed_tools=["Skill", "Read", "Write", "Edit", "Bash", "Grep", "Glob"],  # Enable Skills
                permission_mode="bypassPermissions",  # Allow commands without approval
            )
            logger.info(f"[AGENT] Options configured - model: {model}, max_turns: 10")

            # Create new client instance
            client = ClaudeSDKClient(options)

            # Store client for future use
            if session_id:
                client_sessions[session_id] = client
                logger.info(f"[AGENT] Client stored for session: {session_id}")

        # Run query asynchronously
        logger.info("[AGENT] Creating new event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info("[AGENT] Running agent query...")
            loop.run_until_complete(run_agent_query(user_message, client, session_id))
            logger.info("[AGENT] Agent query completed successfully")
        finally:
            logger.info("[AGENT] Closing event loop")
            loop.close()

    except Exception as e:
        logger.error(f"[AGENT ERROR] Error processing query: {str(e)}", exc_info=True)
        socketio.emit('error', {'message': f'Error: {str(e)}'})


async def run_agent_query(user_message, client, session_id):
    """Run the Agent SDK query and stream responses using ClaudeSDKClient"""
    logger.info("[STREAM] Starting run_agent_query")
    accumulated_text = ""
    current_session_id = session_id
    message_count = 0

    try:
        # Connect client if first time (for new sessions)
        if not hasattr(client, '_connected') or not client._connected:
            logger.info("[STREAM] Connecting client for first time")
            await client.connect()
            client._connected = True
            logger.info("[STREAM] Client connected successfully")

        # Send query to client (maintains conversation context)
        logger.info("[STREAM] Sending query to ClaudeSDKClient")
        await client.query(user_message)
        logger.info("[STREAM] Query sent, receiving responses...")

        # Stream responses from client
        async for message in client.receive_response():
            message_count += 1
            logger.info(f"[STREAM] Received message #{message_count} from Agent SDK")
            logger.info(f"[STREAM] Message object type: {type(message)}")
            logger.info(f"[STREAM] Message attributes: {dir(message)}")
            logger.info(f"[STREAM] Message type: {getattr(message, 'type', 'unknown')}")
            logger.info(f"[STREAM] Message subtype: {getattr(message, 'subtype', 'none')}")

            # Try to log the full message structure for debugging
            if hasattr(message, '__dict__'):
                logger.info(f"[STREAM] Message dict: {message.__dict__}")
            elif hasattr(message, 'model_dump'):
                logger.info(f"[STREAM] Message dump: {message.model_dump()}")
            else:
                logger.info(f"[STREAM] Message repr: {repr(message)}")

            # Capture session ID from init message
            if hasattr(message, 'subtype') and message.subtype == 'init':
                current_session_id = message.data.get('session_id')
                logger.info(f"[STREAM] Init message received")
                if current_session_id:
                    logger.info(f"[STREAM] Session ID: {current_session_id}")

            # Handle assistant messages (text and tool uses)
            message_type = type(message).__name__
            if message_type == 'AssistantMessage' and hasattr(message, 'content'):
                content = message.content
                logger.info(f"[STREAM] Assistant message with {len(content)} content blocks")

                for idx, block in enumerate(content):
                    block_type = type(block).__name__
                    logger.info(f"[STREAM] Block #{idx} type: {block_type}")

                    # Handle text blocks
                    if block_type == 'TextBlock' and hasattr(block, 'text'):
                        text = block.text
                        logger.info(f"[STREAM] Text block #{idx}: {len(text)} chars - '{text[:100]}...'")
                        accumulated_text += text

                        # Stream text chunks to client
                        logger.info(f"[OUTGOING] Emitting assistant_chunk to client")
                        socketio.emit('assistant_chunk', {
                            'text': text,
                            'session_id': current_session_id
                        })

                    # Handle tool use blocks
                    elif block_type == 'ToolUseBlock':
                        tool_name = getattr(block, 'name', None)
                        tool_input = getattr(block, 'input', {})
                        logger.info(f"[STREAM] Tool use detected: {tool_name}")
                        logger.info(f"[STREAM] Tool input: {tool_input}")

                        # Notify client of skill invocation
                        logger.info(f"[OUTGOING] Emitting tool_use to client")
                        socketio.emit('tool_use', {
                            'tool': tool_name,
                            'input': tool_input
                        })

            # Handle user messages (tool results)
            if message_type == 'UserMessage' and hasattr(message, 'content'):
                content = message.content
                for block in content:
                    block_type = type(block).__name__
                    if block_type == 'ToolResultBlock':
                        tool_result = getattr(block, 'content', '')
                        is_error = getattr(block, 'is_error', False)
                        logger.info(f"[STREAM] Tool result received - Error: {is_error}")
                        logger.info(f"[STREAM] Tool result content: {tool_result[:200]}...")

                        # Emit tool result to client
                        logger.info(f"[OUTGOING] Emitting tool_result to client")
                        socketio.emit('tool_result', {
                            'content': tool_result,
                            'is_error': is_error,
                            'session_id': current_session_id
                        })

        # Send completion signal
        logger.info(f"[STREAM] Agent stream completed - processed {message_count} messages")
        logger.info(f"[STREAM] Total accumulated text: {len(accumulated_text)} chars")

        # Save assistant response to database
        if current_session_id and accumulated_text:
            db.save_message(current_session_id, 'assistant', accumulated_text)
            logger.info(f"[DATABASE] Assistant response saved for session {current_session_id}")

        logger.info(f"[OUTGOING] Emitting assistant_complete to client")
        socketio.emit('assistant_complete', {
            'full_text': accumulated_text,
            'session_id': current_session_id
        })

    except Exception as e:
        logger.error(f"[STREAM ERROR] Error in agent query: {str(e)}", exc_info=True)
        logger.info(f"[OUTGOING] Emitting error to client")
        socketio.emit('error', {'message': f'Agent error: {str(e)}'})


async def disconnect_client(session_id):
    """Disconnect and remove a client session"""
    try:
        client = client_sessions.get(session_id)
        if client:
            logger.info(f"Disconnecting client for session: {session_id}")

            # Run disconnect in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                await client.disconnect()
                logger.info(f"Client disconnected successfully: {session_id}")
            finally:
                loop.close()

            # Remove from sessions
            del client_sessions[session_id]
            logger.info(f"Session removed: {session_id}")
    except Exception as e:
        logger.error(f"Error disconnecting client: {str(e)}", exc_info=True)


@socketio.on('clear_session')
def handle_clear_session(data):
    """Clear the current session and disconnect client"""
    session_id = data.get('session_id')
    if session_id and session_id in client_sessions:
        logger.info(f"Clearing session: {session_id}")
        # Disconnect client asynchronously
        socketio.start_background_task(disconnect_client, session_id)
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

    if not session_id:
        emit('error', {'message': 'Session ID required'})
        return

    try:
        logger.info(f"[SESSION] Resuming session: {session_id}")

        # Get session from database
        session_info = db.get_session(session_id)
        if not session_info:
            emit('error', {'message': 'Session not found'})
            return

        # Get conversation history
        history = db.get_session_history(session_id)

        # Create new client that resumes from this session
        model_input = os.getenv('MODEL', 'claude-haiku-4-5-20251001')
        model_mapping = {
            'claude-haiku-4-5': 'claude-haiku-4-5-20251001',
            'haiku': 'claude-haiku-4-5-20251001',
            'claude-sonnet-4-5': 'claude-sonnet-4-5-20250929',
            'sonnet': 'claude-sonnet-4-5-20250929',
        }
        model = model_mapping.get(model_input, model_input)

        options = ClaudeAgentOptions(
            model=model,
            resume=session_id,  # SDK will load conversation history
            max_turns=10,
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": SYSTEM_PROMPT
            },
            setting_sources=["project"],
            allowed_tools=["Skill", "Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            permission_mode="bypassPermissions"
        )

        client = ClaudeSDKClient(options)
        client_sessions[session_id] = client

        # Send session info and history to client
        emit('session_resumed', {
            'session_id': session_id,
            'session_info': session_info,
            'history': history
        })

        logger.info(f"[SESSION] Session {session_id} resumed successfully with {len(history)} messages")

    except Exception as e:
        logger.error(f"[SESSION ERROR] Error resuming session {session_id}: {e}", exc_info=True)
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
        if session_id in client_sessions:
            del client_sessions[session_id]

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


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Demand Forecasting Chatbot Server')
    parser.add_argument('--model', type=str,
                       help='Claude model to use (default: claude-haiku-4-5, options: claude-haiku-4-5 or haiku, claude-sonnet-4-5 or sonnet)')
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
    logger.info("=" * 60)
    logger.info("Starting Demand Forecasting Chatbot Server")
    logger.info("=" * 60)
    logger.info(f"Model: {model}")
    logger.info(f"Port: {port}")
    logger.info(f"URL: http://localhost:{port}")
    logger.info("=" * 60)

    # Run with threading mode
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
