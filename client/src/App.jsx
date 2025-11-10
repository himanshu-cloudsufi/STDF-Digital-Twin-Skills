import useSocket from './hooks/useSocket';
import Sidebar from './features/sidebar/Sidebar';
import Header from './features/header/Header';
import ChatContainer from './features/chat/ChatContainer';
import InputArea from './features/chat/InputArea';
import ComparisonModal from './features/comparison/ComparisonModal';
import ArtifactPanel from './features/chat/ArtifactPanel';

function App() {
  // Initialize WebSocket connection
  useSocket();

  return (
    <div className="w-full h-screen bg-white flex flex-row overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header spans full width */}
        <Header />

        {/* Content area below header with chat and panel side-by-side */}
        <div className="flex-1 flex flex-row overflow-hidden">
          {/* Main chat area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <ChatContainer />
            <InputArea />
          </div>

          {/* Artifact panel slides in from right */}
          <ArtifactPanel />
        </div>
      </div>

      <ComparisonModal />
    </div>
  );
}

export default App;
