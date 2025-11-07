import useStore from '../../store/useStore';
import ConnectionStatus from './ConnectionStatus';
import { exportToMarkdown } from '../export/exportToMarkdown';
import { exportToPDF } from '../export/exportToPDF';

const Header = () => {
  const { toggleSidebar, messages, addMessage } = useStore();

  const handleExportMarkdown = () => {
    exportToMarkdown(messages, addMessage);
  };

  const handleExportPDF = () => {
    exportToPDF(messages, addMessage);
  };

  return (
    <header className="flex items-center gap-4 bg-secondary text-white px-5 py-4 border-b border-gray-300">
      <button
        onClick={toggleSidebar}
        className="bg-transparent border-none text-white cursor-pointer p-1 flex items-center justify-center md:hidden"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 12h18M3 6h18M3 18h18" />
        </svg>
      </button>

      <div className="flex-1">
        <h1 className="text-xl font-medium">Demand Forecasting Chatbot</h1>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleExportMarkdown}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-purple border-none rounded text-white text-xs font-medium cursor-pointer transition-colors hover:bg-purple-dark"
          title="Export chat to Markdown"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          MD
        </button>

        <button
          onClick={handleExportPDF}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-success border-none rounded text-white text-xs font-medium cursor-pointer transition-colors hover:bg-success-dark"
          title="Export chat to PDF"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          PDF
        </button>

        <ConnectionStatus />
      </div>
    </header>
  );
};

export default Header;
