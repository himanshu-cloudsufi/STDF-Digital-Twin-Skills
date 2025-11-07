import useStore from '../../store/useStore';

const ConnectionStatus = () => {
  const { connectionStatus, isConnected } = useStore();

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span
        className={`w-2 h-2 rounded-full ${
          isConnected ? 'bg-success' : 'bg-red-500'
        }`}
      />
      <span>{connectionStatus}</span>
    </div>
  );
};

export default ConnectionStatus;
