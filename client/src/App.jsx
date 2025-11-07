import useSocket from './hooks/useSocket';
import Sidebar from './features/sidebar/Sidebar';
import Header from './features/header/Header';
import ChatContainer from './features/chat/ChatContainer';
import InputArea from './features/chat/InputArea';
import ComparisonModal from './features/comparison/ComparisonModal';

function App() {
  // Initialize WebSocket connection
  useSocket();

  return (
    <div className="w-full h-screen bg-white flex flex-row overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <ChatContainer />
        <InputArea />
      </div>

      <ComparisonModal />
    </div>
  );
}

export default App;
