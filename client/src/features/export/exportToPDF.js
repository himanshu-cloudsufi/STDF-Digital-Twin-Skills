import { jsPDF } from 'jspdf';

export const exportToPDF = async (messages, addMessage) => {
  if (messages.length === 0) {
    alert('No messages to export!');
    return;
  }

  try {
    const pdf = new jsPDF('p', 'mm', 'a4');

    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 15;
    const contentWidth = pageWidth - (2 * margin);
    let yPosition = margin;

    // Add title
    pdf.setFontSize(16);
    pdf.setFont(undefined, 'bold');
    pdf.text('Demand Forecasting Chat Export', margin, yPosition);
    yPosition += 10;

    // Add export date
    pdf.setFontSize(10);
    pdf.setFont(undefined, 'normal');
    pdf.setTextColor(100, 100, 100);
    const exportDate = new Date().toLocaleString();
    pdf.text(`Exported: ${exportDate}`, margin, yPosition);
    yPosition += 10;

    // Add separator line
    pdf.setDrawColor(200, 200, 200);
    pdf.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 8;

    // Reset text color
    pdf.setTextColor(0, 0, 0);

    // Process each message
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];
      let text = message.content || '';

      if (!text.trim()) continue;

      // Check if we need a new page
      if (yPosition > pageHeight - 40) {
        pdf.addPage();
        yPosition = margin;
      }

      // Set role styling
      if (message.role === 'user') {
        pdf.setFont(undefined, 'bold');
        pdf.text('User:', margin, yPosition);
        yPosition += 6;
      } else if (message.role === 'assistant') {
        pdf.setFont(undefined, 'bold');
        pdf.text('Assistant:', margin, yPosition);
        yPosition += 6;
      } else if (message.role === 'system') {
        pdf.setFont(undefined, 'bold');
        pdf.text('System:', margin, yPosition);
        yPosition += 6;
      }

      // Reset font for content
      pdf.setFont(undefined, 'normal');

      // Split text into lines that fit the page width
      const lines = pdf.splitTextToSize(text, contentWidth);

      for (let line of lines) {
        // Check if we need a new page
        if (yPosition > pageHeight - 20) {
          pdf.addPage();
          yPosition = margin;
        }

        pdf.text(line, margin + 5, yPosition);
        yPosition += 5;
      }

      // Add spacing between messages
      yPosition += 5;

      // Add separator line between messages
      pdf.setDrawColor(230, 230, 230);
      pdf.line(margin, yPosition, pageWidth - margin, yPosition);
      yPosition += 5;
    }

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const filename = `chat-export-${timestamp}.pdf`;

    // Save the PDF
    pdf.save(filename);

    // Show success message
    addMessage({
      role: 'system',
      content: `Chat exported successfully as ${filename}`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('PDF export error:', error);
    alert('Failed to export PDF. Please try again.');
  }
};
