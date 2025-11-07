"""
Session Persistence Database Manager
SQLite-based storage for chatbot conversations and session management
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


class SessionDatabase:
    """Manages SQLite database for session persistence"""

    def __init__(self, db_path: str = "sessions.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = Path(db_path)
        self.local = threading.local()
        self._init_database()
        logger.info(f"Session database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.local.conn.row_factory = sqlite3.Row

        try:
            yield self.local.conn
        except Exception as e:
            self.local.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        else:
            self.local.conn.commit()

    def _init_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    title TEXT,
                    message_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tool_use_data TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_activity
                ON sessions(last_activity DESC)
            """)

            conn.commit()
            logger.info("Database tables initialized successfully")

    def save_session(self, session_id: str, title: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create or update a session record

        Args:
            session_id: Unique session identifier
            title: Human-readable session title
            metadata: Additional session metadata (JSON-serializable)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if session exists
                cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing session
                    cursor.execute("""
                        UPDATE sessions
                        SET last_activity = CURRENT_TIMESTAMP,
                            title = COALESCE(?, title),
                            metadata = COALESCE(?, metadata)
                        WHERE session_id = ?
                    """, (title, json.dumps(metadata) if metadata else None, session_id))
                else:
                    # Create new session
                    cursor.execute("""
                        INSERT INTO sessions (session_id, title, metadata)
                        VALUES (?, ?, ?)
                    """, (session_id, title or f"Chat {session_id[:8]}",
                          json.dumps(metadata) if metadata else None))

                logger.info(f"Session {'updated' if exists else 'created'}: {session_id}")
                return True

        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session metadata

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session data or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, created_at, last_activity, title,
                           message_count, metadata
                    FROM sessions
                    WHERE session_id = ?
                """, (session_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'session_id': row['session_id'],
                        'created_at': str(row['created_at']) if row['created_at'] else None,
                        'last_activity': str(row['last_activity']) if row['last_activity'] else None,
                        'title': row['title'],
                        'message_count': row['message_count'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    }
                return None

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all sessions ordered by last activity

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip (for pagination)

        Returns:
            List of session dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, created_at, last_activity, title,
                           message_count, metadata
                    FROM sessions
                    ORDER BY last_activity DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'session_id': row['session_id'],
                        'created_at': str(row['created_at']) if row['created_at'] else None,
                        'last_activity': str(row['last_activity']) if row['last_activity'] else None,
                        'title': row['title'],
                        'message_count': row['message_count'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    })

                logger.info(f"Retrieved {len(sessions)} sessions")
                return sessions

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def get_sessions_needing_titles(self) -> List[Dict[str, Any]]:
        """
        Get all sessions that have 3+ messages but no custom title.
        Returns sessions with at least 6 messages (3 user + 3 assistant)
        and either no title or default title pattern "Chat <session_id>".

        Returns:
            List of session dictionaries that need titles
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, created_at, last_activity, title,
                           message_count, metadata
                    FROM sessions
                    WHERE message_count >= 6
                      AND (title IS NULL OR title LIKE 'Chat %')
                    ORDER BY created_at ASC
                """)

                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'session_id': row['session_id'],
                        'created_at': str(row['created_at']) if row['created_at'] else None,
                        'last_activity': str(row['last_activity']) if row['last_activity'] else None,
                        'title': row['title'],
                        'message_count': row['message_count'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    })

                logger.info(f"Found {len(sessions)} sessions needing titles")
                return sessions

        except Exception as e:
            logger.error(f"Error getting sessions needing titles: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Delete messages (cascade should handle this, but explicit is better)
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                deleted_messages = cursor.rowcount

                # Delete session
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                deleted_session = cursor.rowcount

                if deleted_session > 0:
                    logger.info(f"Deleted session {session_id} ({deleted_messages} messages)")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for deletion")
                    return False

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def update_session_title(self, session_id: str, title: str) -> bool:
        """
        Update session title

        Args:
            session_id: Session identifier
            title: New title

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET title = ?, last_activity = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (title, session_id))

                if cursor.rowcount > 0:
                    logger.info(f"Updated title for session {session_id}: {title}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for title update")
                    return False

        except Exception as e:
            logger.error(f"Error updating session title {session_id}: {e}")
            return False

    def save_message(self, session_id: str, role: str, content: str,
                    tool_use_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a message to the conversation history

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_use_data: Optional tool use/result data

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[DB] Saving message: session={session_id}, role={role}, length={len(content)} chars")

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insert message
                cursor.execute("""
                    INSERT INTO messages (session_id, role, content, tool_use_data)
                    VALUES (?, ?, ?, ?)
                """, (session_id, role, content,
                      json.dumps(tool_use_data) if tool_use_data else None))

                message_id = cursor.lastrowid
                logger.info(f"[DB] Message saved with ID: {message_id}")

                # Update message count and last activity
                cursor.execute("""
                    UPDATE sessions
                    SET message_count = message_count + 1,
                        last_activity = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (session_id,))

                logger.info(f"[DB] Session {session_id} updated (message_count incremented)")

                return True

        except Exception as e:
            logger.error(f"[DB ERROR] Error saving message for session {session_id}: {e}", exc_info=True)
            return False

    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (None = all)

        Returns:
            List of message dictionaries ordered by timestamp
        """
        try:
            logger.info(f"[DB] Retrieving history for session {session_id} (limit={limit or 'all'})")

            with self.get_connection() as conn:
                cursor = conn.cursor()

                if limit:
                    cursor.execute("""
                        SELECT id, role, content, timestamp, tool_use_data
                        FROM messages
                        WHERE session_id = ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    """, (session_id, limit))
                else:
                    cursor.execute("""
                        SELECT id, role, content, timestamp, tool_use_data
                        FROM messages
                        WHERE session_id = ?
                        ORDER BY timestamp ASC
                    """, (session_id,))

                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'id': row['id'],
                        'role': row['role'],
                        'content': row['content'],
                        'timestamp': str(row['timestamp']) if row['timestamp'] else None,
                        'tool_use_data': json.loads(row['tool_use_data']) if row['tool_use_data'] else None
                    })

                logger.info(f"[DB] Retrieved {len(messages)} messages for session {session_id}")

                # Log message breakdown
                user_count = sum(1 for m in messages if m['role'] == 'user')
                assistant_count = sum(1 for m in messages if m['role'] == 'assistant')
                logger.info(f"[DB] Breakdown: {user_count} user, {assistant_count} assistant messages")

                return messages

        except Exception as e:
            logger.error(f"[DB ERROR] Error retrieving history for session {session_id}: {e}", exc_info=True)
            return []

    def get_session_count(self) -> int:
        """Get total number of sessions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM sessions")
                return cursor.fetchone()['count']
        except Exception as e:
            logger.error(f"Error counting sessions: {e}")
            return 0

    def close(self):
        """Close database connection"""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
            logger.info("Database connection closed")
