# Multi-Stage Structured Chatbot Implementation Progress

## Overview
Redesigning the financial analyst chatbot to use a multi-stage workflow with rich structured outputs (XML-based artifacts rendered in accordion UI), similar to the reference JSON structure but streamlined and without Prefect dependencies.

## ✅ Completed (Phase 1-3)

### 1. Backend Foundation ✅

#### Created: `/parsers/artifact_parser.py`
**Purpose:** Parse XML artifacts from Claude responses into structured Python objects

**Features:**
- Comprehensive XML parsing for 10 artifact types:
  - Action Plan (list of steps)
  - Knowledge Graph (nodes + relationships)
  - Query Understanding (detailed plan, datasets, missing data)
  - Forecast Data (time series datasets with metadata)
  - Mathematical Analysis (HTML content)
  - Technological Convergence (HTML content)
  - Market Transformation (HTML content)
  - Strategic Implications (HTML content)
  - News Articles (article list with metadata)
  - References (HTML formatted references)

**Key Methods:**
- `parse_all_artifacts(text)` - Extract all artifacts from response text
- Individual parsers for each artifact type
- `strip_xml_tags(text)` - Remove XML, leaving only plain text for display
- Robust error handling with fallback to regex parsing
- Supports CDATA sections for HTML content

**Data Classes:**
- `ActionPlan`, `KnowledgeGraph`, `QueryUnderstanding`, `ForecastData`
- `AnalysisSection`, `NewsArticles`, `References`
- All data classes use `@dataclass` with `asdict()` for easy JSON serialization

---

#### Created: `/core/stage_manager.py`
**Purpose:** Manage multi-stage workflow (polling → ready_for_research → completed)

**Features:**
- `WorkflowStage` enum: POLLING, READY_FOR_RESEARCH, COMPLETED
- `StageContext` dataclass: Tracks session state, artifacts, status
- Stage transition logic with validation
- Stage-specific system prompts embedded in manager
- Required artifacts validation per stage

**Key Methods:**
- `create_stage_context()` - Initialize new workflow
- `transition_to_next_stage()` - Advance workflow
- `get_stage_prompt()` - Get XML instructions for current stage
- `update_context_artifacts()` - Add parsed artifacts
- `validate_stage_completion()` - Check all required artifacts present
- `export_context_to_dict()` - Serialize for database storage

**Stage-Specific Prompts:**
- Polling: Action plan generation instructions
- Ready for Research: Knowledge graph + query understanding format
- Completed: Full analysis with all artifact types

---

### 2. Database Schema Updates ✅

#### Modified: `/database.py`
**New Tables:**

**`stages` table:**
```sql
CREATE TABLE stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    stage_name TEXT NOT NULL,  -- 'polling', 'ready_for_research', 'completed'
    artifacts_json TEXT,        -- Serialized artifacts dict
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',  -- 'active', 'awaiting_approval', 'completed', 'failed'
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)
```

**`artifacts` table:**
```sql
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    stage_id INTEGER,           -- Link to stage
    artifact_type TEXT NOT NULL,  -- 'action_plan', 'knowledge_graph', etc.
    artifact_data TEXT NOT NULL,  -- JSON serialized artifact
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES stages(id) ON DELETE CASCADE
)
```

**New Indexes:**
- `idx_stages_session` on `(session_id, timestamp)` for fast stage retrieval
- `idx_artifacts_session` on `(session_id, artifact_type, timestamp)` for artifact queries

**New Methods:**
- `save_stage(session_id, stage_name, artifacts_json, status)` → stage_id
- `update_stage_status(stage_id, status)` → bool
- `get_session_stages(session_id)` → List[Dict]
- `get_current_stage(session_id)` → Dict | None
- `save_artifact(session_id, artifact_type, artifact_data, stage_id)` → artifact_id
- `get_session_artifacts(session_id, artifact_type=None)` → List[Dict]
- `get_latest_artifact(session_id, artifact_type)` → Dict | None

**Benefits:**
- Separate storage for artifacts enables efficient retrieval by type
- Stage tracking allows resuming workflows mid-process
- Cascade deletes ensure data integrity

---

### 3. System Prompt Engineering ✅

#### Modified: `/system_prompt.txt`
**Added Section:** "XML Structured Output Format"

**Key Additions:**

1. **Multi-Stage Workflow Instructions**
   - Stage 1: Generate action plan, await approval
   - Stage 2: Generate knowledge graph + query understanding
   - Stage 3: Generate comprehensive analysis with all artifacts

2. **XML Format Examples for Each Artifact Type**
   - Action Plan: `<action_plan><step>...</step></action_plan>`
   - Knowledge Graph: `<knowledge_graph><nodes>...<relationships>...`
   - Query Understanding: `<query_understanding><detailed_plan>...`
   - Forecast Data: `<forecast_data><dataset name="..." type="..." units="...">...`
   - Analysis Sections: `<mathematical_analysis><![CDATA[HTML]]></mathematical_analysis>`
   - References: `<references><![CDATA[HTML]]></references>`

3. **CDATA Usage Guidelines**
   - Use `<![CDATA[...]]>` for HTML/markdown content to avoid parsing conflicts
   - Preserves formatting, tables, lists in analysis sections

4. **Business Language Emphasis**
   - Avoid technical jargon in XML content
   - Focus on insights, not methodology
   - Include specific numbers, years, percentages

**Impact:**
- Claude now knows to structure all forecasting responses with XML
- Consistent artifact format across all queries
- Clear separation between display text and structured data

---

## 📋 Remaining Tasks (Phase 4-7)

### 4. Backend Integration (Next Up) 🔄

#### Modify: `/app_messages_api.py`
**Changes Needed:**

1. **Import New Modules**
```python
from parsers import ArtifactParser
from core import StageManager, WorkflowStage
```

2. **Initialize in App**
```python
artifact_parser = ArtifactParser()
stage_manager = StageManager()
```

3. **Enhanced Message Handler**
```python
@socketio.on('message')
def handle_message(data):
    # Current logic: save message, start background task
    # New: Check if session has active workflow context
    #      If yes, resume from current stage
    #      If no, create new context at POLLING stage
```

4. **New Stage-Based Processing**
```python
def process_query_with_stages(user_message, session_id):
    # Get or create stage context
    context = stage_manager.get_context(session_id) or \
              stage_manager.create_stage_context(session_id, user_message, history)

    # Get stage-specific prompt
    stage_prompt = stage_manager.get_stage_prompt(context)

    # Build messages with stage prompt appended to system prompt
    messages = build_messages_with_stage_context(context, stage_prompt)

    # Stream response
    response_text = stream_response_sync(client, messages, container)

    # Parse artifacts from response
    artifacts = artifact_parser.parse_all_artifacts(response_text)

    # Save artifacts to database
    stage_id = db.save_stage(session_id, context.stage.value, artifacts)
    for artifact_type, artifact_data in artifacts.items():
        db.save_artifact(session_id, artifact_type, artifact_data, stage_id)

    # Emit artifacts to frontend
    for artifact_type, artifact_data in artifacts.items():
        socketio.emit(artifact_type, artifact_data, room=session_id)

    # Handle stage transitions
    if context.stage == WorkflowStage.POLLING:
        # Emit 'awaiting_approval' event
        stage_manager.set_context_status(session_id, 'awaiting_approval')
    elif context.stage == WorkflowStage.READY_FOR_RESEARCH:
        # Auto-proceed to COMPLETED
        stage_manager.transition_to_next_stage(session_id)
        # Trigger next processing round
    elif context.stage == WorkflowStage.COMPLETED:
        # Final stage, cleanup
        stage_manager.set_context_status(session_id, 'completed')
```

5. **New Socket Event Handlers**
```python
@socketio.on('approve_action_plan')
def handle_approve_action_plan(data):
    session_id = data['session_id']
    # Transition from POLLING to READY_FOR_RESEARCH
    stage_manager.transition_to_next_stage(session_id)
    # Continue processing
    process_query_with_stages(None, session_id)

@socketio.on('reject_action_plan')
def handle_reject_action_plan(data):
    session_id = data['session_id']
    feedback = data.get('feedback', '')
    # Reset to POLLING with user feedback
    # Re-generate action plan with feedback incorporated
```

6. **New WebSocket Events to Emit**
```python
# Stage transitions
socketio.emit('stage_transition', {'stage': 'polling', 'session_id': session_id})

# Artifacts (one event per type)
socketio.emit('action_plan', {'steps': [...], 'timestamp': ...})
socketio.emit('knowledge_graph', {'nodes': [...], 'relationships': [...]})
socketio.emit('query_understanding', {detailed_plan': ..., 'datasets': [...]})
socketio.emit('forecast_data', {'datasets': [...]})
socketio.emit('mathematical_analysis', {'html': '...'})
socketio.emit('technological_convergence', {'html': '...'})
socketio.emit('market_transformation', {'html': '...'})
socketio.emit('strategic_implications', {'html': '...'})
socketio.emit('news_articles', {'articles': [...]})
socketio.emit('references', {'html': '...'})

# Approval requests
socketio.emit('awaiting_approval', {'message': 'Review action plan. Proceed?'})
```

**Estimated Effort:** 4-6 hours

---

### 5. Frontend UI Components 🎨

#### Modify: `/static/index.html`
**Changes Needed:**

1. **Add Stage Indicator**
```html
<div class="stage-indicator" id="stageIndicator">
  <div class="stage-item" data-stage="polling">
    <span class="stage-dot">1</span>
    <span class="stage-label">Planning</span>
  </div>
  <div class="stage-item" data-stage="ready_for_research">
    <span class="stage-dot">2</span>
    <span class="stage-label">Research</span>
  </div>
  <div class="stage-item" data-stage="completed">
    <span class="stage-dot">3</span>
    <span class="stage-label">Analysis</span>
  </div>
</div>
```

2. **Add Artifact Container Template**
```html
<div class="message assistant">
  <div class="message-header">
    <span class="role">Assistant</span>
    <span class="stage-badge">Polling</span>
  </div>

  <!-- Main response text -->
  <div class="message-content">
    <div class="markdown-content" data-raw-text="">
      <!-- Rendered markdown here -->
    </div>
  </div>

  <!-- Artifacts Accordion -->
  <div class="artifacts-container">
    <!-- Action Plan -->
    <div class="artifact-section" data-type="action-plan" style="display: none;">
      <button class="artifact-toggle">
        <span class="icon">▶</span>
        <span class="label">Action Plan</span>
        <span class="badge">0 steps</span>
      </button>
      <div class="artifact-content collapsed">
        <ol class="action-plan-list"></ol>
      </div>
    </div>

    <!-- Knowledge Graph -->
    <div class="artifact-section" data-type="knowledge-graph" style="display: none;">
      <button class="artifact-toggle">
        <span class="icon">▶</span>
        <span class="label">Knowledge Graph</span>
        <span class="badge">0 nodes, 0 relationships</span>
      </button>
      <div class="artifact-content collapsed">
        <div class="knowledge-graph-viz"></div>
      </div>
    </div>

    <!-- Forecast Data -->
    <div class="artifact-section" data-type="forecast-data" style="display: none;">
      <button class="artifact-toggle">
        <span class="icon">▶</span>
        <span class="label">Forecast Data</span>
        <span class="badge">0 datasets</span>
      </button>
      <div class="artifact-content collapsed">
        <div class="forecast-tables"></div>
      </div>
    </div>

    <!-- Analysis Sections -->
    <div class="artifact-section" data-type="mathematical-analysis" style="display: none;">
      <button class="artifact-toggle">
        <span class="icon">▶</span>
        <span class="label">Mathematical Analysis</span>
      </button>
      <div class="artifact-content collapsed"></div>
    </div>

    <!-- Similar sections for convergence, transformation, strategic -->
  </div>

  <!-- Approval Controls (only for action plan stage) -->
  <div class="approval-controls" style="display: none;">
    <button class="approve-button">Approve & Proceed</button>
    <button class="reject-button">Revise Plan</button>
  </div>
</div>
```

#### Modify: `/static/style.css`
**New Styles Needed:**

```css
/* Stage Indicator */
.stage-indicator {
  display: flex;
  justify-content: center;
  padding: 20px;
  gap: 40px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.stage-item.active {
  opacity: 1;
}

.stage-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  transition: background 0.3s;
}

.stage-item.active .stage-dot {
  background: #007bff;
  color: white;
}

/* Artifacts Container */
.artifacts-container {
  margin-top: 16px;
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}

.artifact-section {
  margin-bottom: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.artifact-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  transition: background 0.2s;
}

.artifact-toggle:hover {
  background: #e9ecef;
}

.artifact-toggle .icon {
  font-size: 12px;
  transition: transform 0.2s;
}

.artifact-toggle.expanded .icon {
  transform: rotate(90deg);
}

.artifact-toggle .label {
  flex: 1;
}

.artifact-toggle .badge {
  font-size: 12px;
  font-weight: normal;
  color: #6c757d;
  padding: 2px 8px;
  background: #dee2e6;
  border-radius: 12px;
}

.artifact-content {
  padding: 0;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, padding 0.3s ease;
}

.artifact-content.expanded {
  padding: 16px;
  max-height: 2000px;  /* Adjust based on content */
}

/* Approval Controls */
.approval-controls {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.approve-button,
.reject-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.approve-button {
  background: #28a745;
  color: white;
}

.approve-button:hover {
  background: #218838;
}

.reject-button {
  background: #dc3545;
  color: white;
}

.reject-button:hover {
  background: #c82333;
}

/* Knowledge Graph Visualization */
.knowledge-graph-viz {
  /* To be styled based on visualization library */
}

/* Forecast Tables */
.forecast-tables table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.forecast-tables th,
.forecast-tables td {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  text-align: left;
}

.forecast-tables th {
  background: #f8f9fa;
  font-weight: 600;
}
```

**Estimated Effort:** 3-4 hours

---

### 6. Frontend Event Handlers & Rendering 🎮

#### Modify: `/static/chat.js`
**New Functions Needed:**

```javascript
// Stage Management
function handleStageTransition(data) {
  const { stage, session_id } = data;
  const stageIndicator = document.getElementById('stageIndicator');

  // Update active stage dot
  stageIndicator.querySelectorAll('.stage-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.stage === stage) {
      item.classList.add('active');
    }
  });

  // Update stage badge on current message
  const currentMessage = document.querySelector('.message.assistant:last-child');
  if (currentMessage) {
    const badge = currentMessage.querySelector('.stage-badge');
    badge.textContent = stage === 'polling' ? 'Planning' :
                       stage === 'ready_for_research' ? 'Research' : 'Analysis';
  }
}

// Action Plan Rendering
function handleActionPlan(data) {
  const { steps, timestamp } = data;
  const currentMessage = document.querySelector('.message.assistant:last-child');
  const section = currentMessage.querySelector('.artifact-section[data-type="action-plan"]');

  // Show section
  section.style.display = 'block';

  // Update badge
  const badge = section.querySelector('.badge');
  badge.textContent = `${steps.length} steps`;

  // Render steps
  const list = section.querySelector('.action-plan-list');
  list.innerHTML = '';
  steps.forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    list.appendChild(li);
  });

  // Show approval controls
  const approvalControls = currentMessage.querySelector('.approval-controls');
  approvalControls.style.display = 'flex';
}

// Knowledge Graph Rendering
function handleKnowledgeGraph(data) {
  const { nodes, relationships } = data;
  const currentMessage = document.querySelector('.message.assistant:last-child');
  const section = currentMessage.querySelector('.artifact-section[data-type="knowledge-graph"]');

  section.style.display = 'block';

  // Update badge
  const badge = section.querySelector('.badge');
  badge.textContent = `${nodes.length} nodes, ${relationships.length} relationships`;

  // Render as table (or use D3.js for graph visualization)
  const viz = section.querySelector('.knowledge-graph-viz');
  let html = '<h4>Nodes</h4><table><thead><tr><th>Name</th><th>Type</th><th>Relevance</th></tr></thead><tbody>';

  nodes.forEach(node => {
    html += `<tr><td>${node.name}</td><td>${node.label}</td><td>${node.relevance}</td></tr>`;
  });

  html += '</tbody></table><h4>Relationships</h4><table><thead><tr><th>Type</th><th>From → To</th><th>Relevance</th></tr></thead><tbody>';

  relationships.forEach(rel => {
    const startNode = nodes.find(n => n.id === rel.start_node);
    const endNode = nodes.find(n => n.id === rel.end_node);
    html += `<tr><td>${rel.type}</td><td>${startNode?.name} → ${endNode?.name}</td><td>${rel.relevance}</td></tr>`;
  });

  html += '</tbody></table>';
  viz.innerHTML = html;
}

// Forecast Data Rendering
function handleForecastData(data) {
  const { datasets } = data;
  const currentMessage = document.querySelector('.message.assistant:last-child');
  const section = currentMessage.querySelector('.artifact-section[data-type="forecast-data"]');

  section.style.display = 'block';

  const badge = section.querySelector('.badge');
  badge.textContent = `${datasets.length} datasets`;

  const container = section.querySelector('.forecast-tables');
  let html = '';

  datasets.forEach(dataset => {
    html += `<h4>${dataset.name}</h4>`;
    html += `<p><em>${dataset.description}</em></p>`;
    html += '<table><thead><tr><th>Year</th><th>Value</th></tr></thead><tbody>';

    dataset.x.forEach((year, i) => {
      html += `<tr><td>${year}</td><td>${dataset.y[i].toLocaleString()} ${dataset.units}</td></tr>`;
    });

    html += '</tbody></table>';
  });

  container.innerHTML = html;
}

// Analysis Section Rendering
function handleAnalysisArtifact(type, data) {
  const { html } = data;
  const currentMessage = document.querySelector('.message.assistant:last-child');
  const section = currentMessage.querySelector(`.artifact-section[data-type="${type}"]`);

  if (!section) return;

  section.style.display = 'block';
  const content = section.querySelector('.artifact-content');
  content.innerHTML = html;  // Already sanitized HTML from CDATA
}

// Accordion Toggle
function toggleArtifact(artifactType) {
  const section = document.querySelector(`.artifact-section[data-type="${artifactType}"]`);
  const toggle = section.querySelector('.artifact-toggle');
  const content = section.querySelector('.artifact-content');

  toggle.classList.toggle('expanded');
  content.classList.toggle('expanded');
}

// Approval Actions
function approveActionPlan(sessionId) {
  socket.emit('approve_action_plan', { session_id: sessionId });

  // Hide approval controls
  const approvalControls = document.querySelector('.approval-controls');
  approvalControls.style.display = 'none';

  // Show loading indicator
  addSystemMessage('Action plan approved. Generating detailed analysis...');
}

function rejectActionPlan(sessionId) {
  const feedback = prompt('Please provide feedback for plan revision:');
  if (!feedback) return;

  socket.emit('reject_action_plan', { session_id: sessionId, feedback });

  addSystemMessage('Revising action plan based on your feedback...');
}

// Socket Event Listeners
socket.on('stage_transition', handleStageTransition);
socket.on('action_plan', handleActionPlan);
socket.on('knowledge_graph', handleKnowledgeGraph);
socket.on('query_understanding', handleQueryUnderstanding);
socket.on('forecast_data', handleForecastData);
socket.on('mathematical_analysis', (data) => handleAnalysisArtifact('mathematical-analysis', data));
socket.on('technological_convergence', (data) => handleAnalysisArtifact('technological-convergence', data));
socket.on('market_transformation', (data) => handleAnalysisArtifact('market-transformation', data));
socket.on('strategic_implications', (data) => handleAnalysisArtifact('strategic-implications', data));
socket.on('news_articles', handleNewsArticles);
socket.on('references', handleReferences);

// Accordion click handlers
document.addEventListener('click', (e) => {
  if (e.target.closest('.artifact-toggle')) {
    const section = e.target.closest('.artifact-section');
    const type = section.dataset.type;
    toggleArtifact(type);
  }

  if (e.target.closest('.approve-button')) {
    approveActionPlan(sessionId);
  }

  if (e.target.closest('.reject-button')) {
    rejectActionPlan(sessionId);
  }
});
```

**Estimated Effort:** 5-6 hours

---

### 7. Testing & Polish 🧪

**Testing Checklist:**
- [ ] Test action plan generation and approval flow
- [ ] Test knowledge graph rendering (nodes + relationships)
- [ ] Test forecast data tables with multiple datasets
- [ ] Test all 4 analysis sections (mathematical, convergence, transformation, strategic)
- [ ] Test accordion expand/collapse
- [ ] Test stage transitions (polling → research → completed)
- [ ] Test session resume with stages preserved
- [ ] Test artifact persistence to database
- [ ] Test error handling (malformed XML, missing artifacts)
- [ ] Test responsive layout on different screen sizes

**Polish Tasks:**
- [ ] Add loading states for each stage
- [ ] Add transition animations between stages
- [ ] Add empty state messages ("No artifacts available")
- [ ] Add error messages for failed parsing
- [ ] Add tooltips for stage indicators
- [ ] Add copy-to-clipboard for forecast data
- [ ] Improve accessibility (ARIA labels, keyboard navigation)
- [ ] Add export functionality (include artifacts in PDF/MD)

**Documentation:**
- [ ] Update README with new architecture
- [ ] Document XML format for future reference
- [ ] Create user guide for multi-stage workflow
- [ ] Add inline code comments

**Estimated Effort:** 4-5 hours

---

## Total Effort Estimate

| Phase | Status | Estimated Time |
|-------|--------|----------------|
| 1-3: Foundation (Completed) | ✅ | ~8 hours |
| 4: Backend Integration | 🔄 | 4-6 hours |
| 5: Frontend UI | 🔄 | 3-4 hours |
| 6: Event Handlers | 🔄 | 5-6 hours |
| 7: Testing & Polish | 🔄 | 4-5 hours |
| **Total Remaining** | | **16-21 hours** |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│ USER QUERY                                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ STAGE MANAGER (core/stage_manager.py)                       │
│ ├─ Create context: POLLING stage                            │
│ ├─ Get stage-specific prompt                                │
│ └─ Track artifacts per stage                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ CLAUDE API (with XML prompt)                                │
│ Returns response with XML artifacts:                         │
│ <action_plan>...</action_plan>                              │
│ <knowledge_graph>...</knowledge_graph>                      │
│ <forecast_data>...</forecast_data>                          │
│ <mathematical_analysis><![CDATA[...]]></mathematical_analysis>│
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ ARTIFACT PARSER (parsers/artifact_parser.py)                │
│ ├─ Extract XML from response text                           │
│ ├─ Parse into Python objects                                │
│ └─ Convert to JSON for emission                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ DATABASE (database.py)                                      │
│ ├─ Save stage: stages table                                │
│ ├─ Save artifacts: artifacts table                         │
│ └─ Link artifacts to stage via foreign key                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ WEBSOCKET EVENTS                                            │
│ ├─ stage_transition → Update UI progress                   │
│ ├─ action_plan → Render accordion with steps               │
│ ├─ knowledge_graph → Render nodes + relationships          │
│ ├─ forecast_data → Render data tables                      │
│ ├─ *_analysis → Render HTML analysis sections              │
│ └─ awaiting_approval → Show approve/reject buttons         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ FRONTEND UI (static/index.html, chat.js, style.css)        │
│ ├─ Stage indicator (3 dots showing progress)               │
│ ├─ Accordion sections (collapsible artifacts)              │
│ ├─ Approval controls (approve/reject buttons)              │
│ └─ Real-time artifact rendering                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

1. **XML over JSON**: Easier to embed HTML/markdown in CDATA sections, cleaner for Claude to generate
2. **Server-side parsing**: More robust than client-side, enables database storage, reduces client load
3. **Separate artifact storage**: Enables efficient querying, better data integrity
4. **Accordion UI**: Progressive disclosure, doesn't overwhelm user, familiar pattern
5. **Hybrid streaming**: Continue streaming text for responsiveness, emit complete artifacts when ready
6. **Stage-based approval**: Only require approval for action plan (Stage 1), auto-proceed for Stages 2-3

---

## Next Steps

1. **Review this progress** with stakeholders
2. **Decide on frontend visualization** for knowledge graph (table vs D3.js graph)
3. **Continue with Backend Integration** (Phase 4)
4. **Implement Frontend UI** (Phase 5)
5. **Wire up Event Handlers** (Phase 6)
6. **Test & Polish** (Phase 7)

---

## Files Created/Modified

### Created:
- `/parsers/__init__.py`
- `/parsers/artifact_parser.py` (580 lines)
- `/core/__init__.py`
- `/core/stage_manager.py` (320 lines)
- `/schemas/` (directory for future XSD schemas)
- `/static/components/` (directory for reusable JS components)

### Modified:
- `/database.py` (+330 lines: new tables, methods)
- `/system_prompt.txt` (+185 lines: XML format instructions)

### To Modify:
- `/app_messages_api.py` (integrate stage manager, artifact parser, new events)
- `/static/index.html` (stage indicator, accordion structure)
- `/static/chat.js` (event handlers, rendering functions)
- `/static/style.css` (accordion, stage indicator styles)

---

**Status:** ✅ Foundation complete, ready for integration phase
