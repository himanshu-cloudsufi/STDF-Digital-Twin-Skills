import useStore from '../../store/useStore';
import SessionItem from './SessionItem';

const SessionList = () => {
  const { sessions, sessionId, isCompareMode, selectedSessions } = useStore();

  if (sessions.length === 0) {
    return (
      <div className="text-center p-5 text-gray-600 text-xs">
        No saved conversations
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-2.5 custom-scrollbar">
      {sessions.map((session) => (
        <SessionItem
          key={session.session_id}
          session={session}
          isActive={session.session_id === sessionId}
          isCompareMode={isCompareMode}
          isSelected={selectedSessions.includes(session.session_id)}
        />
      ))}
    </div>
  );
};

export default SessionList;
