export const exportToMarkdown = (messages, addMessage) => {
  if (messages.length === 0) {
    alert('No messages to export!');
    return;
  }

  try {
    let markdown = '# Demand Forecasting Chat Export\n\n';
    markdown += `**Exported:** ${new Date().toLocaleString()}\n\n`;
    markdown += '---\n\n';

    messages.forEach((message) => {
      if (message.role === 'user') {
        markdown += '## 👤 User\n\n';
        markdown += message.content + '\n\n';
        markdown += '---\n\n';
      } else if (message.role === 'assistant') {
        markdown += '## 🤖 Assistant\n\n';
        markdown += message.content + '\n\n';
        markdown += '---\n\n';
      } else if (message.role === 'system') {
        markdown += '## ⚙️ System\n\n';
        markdown += message.content + '\n\n';
        markdown += '---\n\n';
      }
    });

    // Create blob and download
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    a.download = `chat-export-${timestamp}.md`;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Show success message
    addMessage({
      role: 'system',
      content: `Chat exported successfully as ${a.download}`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Markdown export error:', error);
    alert('Failed to export Markdown. Please try again.');
  }
};
