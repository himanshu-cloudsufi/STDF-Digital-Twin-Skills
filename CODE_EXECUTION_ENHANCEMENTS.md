# Code Execution & Tool Use Visibility Enhancements

## Overview

The forecasting chatbot now provides **real-time visibility** into code execution, tool usage, bash commands, and Claude's thinking process on the frontend. Users can see exactly what's happening behind the scenes as Claude processes their requests.

## New Visibility Features (Latest Update)

### Real-Time Code Execution & Tool Use Display

The chatbot now shows **exactly what's happening** as Claude processes requests:

#### 1. **Code Execution Blocks**
When Claude runs Python code, you'll see:
- ⚙️ **Code Execution** header with real-time status
- **Running** status (blue badge with pulsing animation)
- **Input Parameters** showing the code/commands being executed
- **Completed** status (green badge) when done
- Collapsible interface to hide/show details

#### 2. **Tool Use Visualization**
When Claude uses forecasting skills or other tools:
- 🔧 **Tool Name** displayed prominently
- **Parameters** streamed in real-time as they're constructed
- JSON parameters with syntax highlighting
- Dark-themed code blocks for readability

#### 3. **Extended Thinking Display** (if enabled)
- 💭 **Thinking Process** shows Claude's reasoning
- Collapsible block to avoid clutter
- Monospace text for code-like thinking
- Amber theme to differentiate from regular content

#### 4. **Status Indicators**
- **Running**: Blue badge with pulse animation
- **Completed**: Green badge
- **Error**: Red badge (ready for error handling)

### User Benefits
- ✅ **Transparency**: See exactly what commands/code are being run
- ✅ **Trust**: Understand how Claude is processing your request
- ✅ **Debugging**: Identify issues by seeing tool parameters
- ✅ **Learning**: Understand how forecasting skills work
- ✅ **Performance**: See what's taking time (tool execution vs text generation)

---

## Previous Features (File Upload/Analysis)

The chatbot has enhanced capabilities using the Anthropic Code Execution tool for file upload, analysis, and visualization.

## All Features

### 1. File Upload & Analysis
Users can now upload CSV, Excel, JSON, and other data files for analysis.

**Supported File Types:**
- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)
- XML (.xml)
- Text (.txt)

**How It Works:**
1. User clicks the green upload button (↑ icon) next to the message input
2. Selects a file to upload
3. Specifies what they want to know about the data
4. Claude analyzes the file using Python (pandas, numpy, matplotlib, etc.)
5. Results are displayed in the chat

**Example Use Cases:**
- "I have EV sales data for 2024 - validate it for forecasting"
- "Analyze this CSV and create visualizations"
- "Compare my data with existing catalog data"
- "Calculate summary statistics and check for missing values"

### 2. Automatic Visualization Generation
Claude can create charts and graphs from forecast data or uploaded files.

**What Claude Can Generate:**
- Line charts for EV adoption curves
- Stacked area charts for market share
- Cost parity trend lines
- Multi-region comparisons
- Custom visualizations based on data

**Example Prompts:**
- "Create a visualization of the BEV forecast"
- "Generate charts showing the tipping point analysis"
- "Visualize the energy generation mix over time"

### 3. File Download Support
Any files Claude generates (charts, reports, processed data) can be downloaded.

**How It Works:**
1. Claude generates files during analysis (e.g., `forecast_chart.png`)
2. Download buttons appear automatically in the chat
3. Click to download the file to your computer

### 4. Enhanced Data Processing
Claude can now perform complex data operations:
- Merge uploaded data with catalog data
- Recalculate forecasts with custom data
- Validate data quality and structure
- Generate custom reports

## Architecture Changes

### Backend (Python)

**New Files:**
- `file_handler.py` - Handles file upload/download via Anthropic Files API

**Modified Files:**
- `app_messages_api.py` - Added 3 new SocketIO handlers:
  - `upload_file` - Receives file from client
  - `download_file` - Sends generated file to client
  - `process_file_upload` - Background processing

**New Dependencies Required:**
```bash
# Already in requirements.txt:
# anthropic (with Files API support)
```

### Frontend (JavaScript/HTML)

**Modified Files:**
- `static/index.html` - Added file upload button
- `static/chat.js` - Added file upload/download functions
- `static/style.css` - Added styling for upload/download UI

**New Functions:**
- `handleFileSelect()` - Processes file selection
- `uploadFile()` - Sends file to server
- `addFileDownloadButtons()` - Creates download buttons
- `requestFileDownload()` - Requests file from server
- `downloadFileFromBase64()` - Handles browser download

## Usage Examples

### Example 1: Upload Custom EV Sales Data

```
User Action:
1. Click upload button (green ↑ icon)
2. Select "china_ev_sales_2024.csv"
3. Enter: "Validate this data and merge it with existing catalog data for China"

Claude Response:
- Validates CSV structure
- Checks for missing values
- Merges with catalog data
- Shows updated forecast
- Provides download link for merged dataset
```

### Example 2: Generate Forecast Visualizations

```
User Message:
"Run a forecast for China EVs through 2040 and create visualizations showing:
1. BEV adoption curve
2. Market share evolution
3. Cost parity timeline"

Claude Response:
- Runs forecast using demand-forecasting skill
- Creates 3 PNG charts using matplotlib
- Provides download buttons for each chart
- Includes analysis in text
```

### Example 3: Custom Data Analysis

```
User Action:
1. Upload "battery_cost_trends.xlsx"
2. Request: "Analyze cost trends and project when costs will drop below $50/kWh"

Claude Response:
- Loads Excel data using pandas
- Performs regression analysis
- Calculates crossover year
- Creates trend visualization
- Provides downloadable report
```

## Technical Details

### Files API Integration

**Upload Flow:**
```
Client (Browser)
  └─> Base64 encode file
  └─> Send via SocketIO to Flask server
      └─> Decode base64
      └─> Upload to Anthropic Files API
          └─> Get file_id
          └─> Send to Messages API with code_execution tool
              └─> Claude analyzes with Python
              └─> Return results + generated file IDs
```

**Download Flow:**
```
Client requests file_id
  └─> Server retrieves from Anthropic Files API
      └─> Encode as base64
      └─> Send to client via SocketIO
          └─> Client decodes and triggers browser download
```

### Code Execution Environment

Your chatbot has access to a sandboxed Python environment with:

**Pre-installed Libraries:**
- **Data Science**: pandas, numpy, scipy, scikit-learn, statsmodels
- **Visualization**: matplotlib, seaborn
- **File Processing**: openpyxl, xlsxwriter, xlrd, pillow
- **Math**: sympy, mpmath

**Resource Limits:**
- Memory: 5GiB RAM
- Disk: 5GiB storage
- CPU: 1 CPU
- No internet access (security)

**Container Lifecycle:**
- Containers expire after 30 days
- Can be reused across requests in a session
- Scoped to your API key workspace

## Best Practices

### For Users

1. **Be Specific in Requests**
   - ❌ "Analyze this file"
   - ✅ "Validate this EV sales data for forecasting and check for missing values"

2. **Provide Context**
   - Include region, time period, data source
   - Specify desired output format
   - Mention if comparing with existing data

3. **Iterative Refinement**
   - Upload data first, review analysis
   - Ask follow-up questions
   - Request specific visualizations

### For Development

1. **Error Handling**
   - All file operations have try/except blocks
   - User-friendly error messages
   - Logging for debugging

2. **Security**
   - Files are sandboxed in Anthropic environment
   - No direct file system access
   - Base64 encoding for transmission

3. **Performance**
   - Background processing for uploads
   - Streaming responses
   - Progress notifications

## Troubleshooting

### File Upload Issues

**Problem:** "File upload failed"
- Check file size (< 5MB recommended)
- Verify file format is supported
- Check browser console for errors

**Problem:** "File analysis timed out"
- Large files may take longer
- Simplify analysis request
- Try smaller data subset

### Download Issues

**Problem:** "Download failed"
- Check if file was actually generated
- Look for error messages in chat
- Verify browser allows downloads

### Code Execution Issues

**Problem:** "Execution time exceeded"
- Code execution has time limits
- Simplify analysis
- Process data in chunks

## Future Enhancements

Potential additions:

1. **Report Generation**
   - PDF reports with charts and analysis
   - Excel workbooks with multiple sheets
   - HTML reports for sharing

2. **Batch Processing**
   - Upload multiple files at once
   - Process entire datasets
   - Generate comparison reports

3. **Container Reuse**
   - Maintain state across session
   - Faster subsequent analyses
   - Iterative data exploration

4. **Advanced Analytics**
   - Custom forecasting models
   - Sensitivity analysis
   - What-if scenarios

## API References

### Backend SocketIO Events

**Client → Server:**
```javascript
socket.emit('upload_file', {
    file_data: base64String,
    filename: 'data.csv',
    session_id: sessionId,
    analysis_request: 'Analyze this data'
});

socket.emit('download_file', {
    file_id: 'file_abc123'
});
```

**Server → Client:**
```javascript
socket.on('file_upload_processing', (data) => {
    // data.filename, data.session_id
});

socket.on('file_analysis_complete', (data) => {
    // data.analysis, data.generated_files, data.file_id
});

socket.on('file_download_ready', (data) => {
    // data.filename, data.file_data (base64)
});
```

### FileUploadHandler Methods

```python
# In file_handler.py

handler = FileUploadHandler(anthropic_client, socketio)

result = handler.upload_and_analyze(
    file_data=bytes,
    filename='data.csv',
    session_id='session_123',
    analysis_request='Validate data'
)

# Returns:
# {
#     'success': True,
#     'analysis': 'Analysis text...',
#     'generated_files': [{'file_id': '...', 'type': 'image'}],
#     'file_id': 'original_file_id'
# }
```

## Testing the Feature

### Quick Test

1. Start your server:
   ```bash
   python3 app_messages_api.py
   ```

2. Open http://localhost:8000

3. Click the green upload button (↑ icon)

4. Create a test CSV file (`test_data.csv`):
   ```csv
   Year,BEV_Sales,ICE_Sales
   2020,100,900
   2021,150,850
   2022,220,780
   2023,350,650
   ```

5. Upload and request: "Analyze this EV sales data and create a visualization"

6. Verify:
   - Analysis appears in chat
   - Download button shows if chart created
   - Can download generated files

## Summary

You now have a **fully integrated file upload/download system** that leverages Claude's code execution capabilities. Users can:

✅ Upload their own data files
✅ Get Python-powered analysis with pandas/numpy/matplotlib
✅ Generate visualizations and reports
✅ Download all generated files
✅ Iterate on analysis with follow-up questions

All without leaving the chat interface!
