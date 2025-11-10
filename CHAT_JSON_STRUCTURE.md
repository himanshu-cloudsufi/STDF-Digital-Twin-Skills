# Chat JSON Structure Documentation

## Overview
This document describes the structure of the chat conversation JSON used in the forecasting system. The JSON contains a conversation history between a user and an AI assistant, with rich structured data including forecasts, analysis, and visualizations.

## Root Structure

```json
{
  "data": [
    {
      "role": "string",
      "content": "string | JSON string",
      "timestamp": "ISO 8601 datetime"
    }
  ]
}
```

## Message Types

### 1. User Messages
Simple messages from the user with plain text content.

```json
{
  "role": "user",
  "content": "when will lead demand peak in china",
  "timestamp": "2025-10-28T07:13:41.961345"
}
```

### 2. Assistant Messages
Complex messages containing structured JSON data as stringified content.

## Assistant Message Content Structure

Assistant messages contain a stringified JSON object with the following fields:

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `flow_run_id` | string (UUID) | Unique identifier for the current flow execution |
| `chat_id` | string | Unique identifier for the chat session |
| `stage` | string | Current stage of processing (e.g., "polling", "ready_for_research", "completed") |
| `chat_type` | string | Type of chat (e.g., "compass") |
| `next_flow` | string \| null | Next flow to execute (e.g., "stellar_generic_follow_up") |
| `artifacts` | string[] | List of artifact types included in this message |
| `timestamp` | string | ISO 8601 timestamp with timezone |
| `is_acknowledged` | boolean | Whether the message has been acknowledged |

### Stage Types

1. **polling** - Initial stage, processing user query
2. **ready_for_research** - Query understood, ready to gather data
3. **completed** - Analysis complete, final response ready

## Artifact Types

### 1. Action Plan (`action-plan`)

**Field:** `action_plan`
**Type:** string[]
**Description:** List of steps to analyze the query

```json
{
  "action_plan": [
    "Analyze S-curve adoption patterns for EV segments using sales and fleet data to identify tipping points.",
    "Evaluate cost curves driving adoption by examining battery pack costs.",
    "Quantify displacement of ICE vehicles using ICE sales data.",
    "Forecast peak demand as market saturation approaches 80-90% penetration."
  ]
}
```

### 2. Knowledge Graph (`knowledge_graph`)

**Field:** `knowledge_graph`
**Type:** object
**Description:** Graph structure representing entities and relationships

```json
{
  "knowledge_graph": {
    "nodes": [
      {
        "id": "UUID",
        "labels": ["NewProduct" | "IncumbentProduct" | "Country" | "Curve" | "NewTechnology" | "Sector" | "Commodity" | "Policy"],
        "properties": {
          "name": "string",
          "relevance": "string",
          "description": "string"
        },
        "caption": "string"
      }
    ],
    "relationships": [
      {
        "id": "UUID",
        "type": "ENABLE" | "IMPACT" | "DRIVES" | "REPLACES" | "ENABLES" | "ACCELERATES" | "BELONGS",
        "start_node": "UUID",
        "end_node": "UUID",
        "properties": {
          "relevance": "string"
        }
      }
    ]
  }
}
```

#### Node Types
- **NewProduct**: Disruptor technologies (EVs, batteries)
- **IncumbentProduct**: Legacy technologies (ICE vehicles, lead-acid batteries)
- **Country**: Geographic regions
- **Curve**: Data curves/datasets
- **NewTechnology**: Enabling technologies
- **Sector**: Industry sectors
- **Commodity**: Raw materials (lithium, copper, etc.)
- **Policy**: Government policies and regulations

#### Relationship Types
- **ENABLE**: Technology enables product
- **IMPACT**: Product impacts region/market
- **DRIVES**: Product drives data curve
- **REPLACES**: Technology replaces incumbent
- **ENABLES**: Commodity enables technology
- **ACCELERATES**: Policy accelerates technology
- **BELONGS**: Sector belongs to region

### 3. Query Understanding (`query-understanding`)

**Field:** `detailed_plan`
**Type:** string (markdown)
**Description:** Detailed analysis plan with disruption framework context

**Field:** `confirmation_query`
**Type:** string
**Description:** Question to confirm plan with user

**Field:** `datasets`
**Type:** string[]
**Description:** List of available datasets to use

**Field:** `missing_datasets`
**Type:** string[]
**Description:** List of datasets needed but not available

```json
{
  "detailed_plan": "# Disruption Analysis Plan for EV Demand Peak in China\n\n## Analysis Approach\n...",
  "confirmation_query": "Does this proposed analysis plan align with your query?",
  "datasets": [
    "Passenger_Vehicle_(EV)_Annual_Sales_China",
    "Lithium_Ion_Battery_Pack_Median_Cost_China"
  ],
  "missing_datasets": [
    "Direct forecasts of EV demand peaking years in China",
    "Granular adoption metrics for autonomous EVs in China"
  ]
}
```

### 4. Forecast Data (`forecast-data`)

**Field:** `forecast_data`
**Type:** object[]
**Description:** Array of dataset forecasts with metadata

```json
{
  "forecast_data": [
    {
      "dataset_name": "string",
      "description": "string",
      "x": [years],
      "y": [values],
      "type": "adoption" | "cost",
      "units": "string",
      "source": "string",
      "region": "China" | "USA" | "Europe" | "Rest_of_World" | "Global",
      "category": "annual adoption" | "cost",
      "entity_type": "disruptor" | "incumbent" | "chimera",
      "level_name": "string",
      "tipping_point": number | null,
      "t80_value": number | null,
      "market_potential_value": number | null,
      "market_potential_unit": "string" | null,
      "market_potential_analysis": "string" | null,
      "tipping_point_basis": "string" | null,
      "tipping_point_analysis": "string" | null,
      "forecast_metadata": {
        "original_end_year": number,
        "forecast_start_year": number,
        "forecast_end_year": number,
        "forecasted_points": number,
        "method": "string",
        "timestamp": "ISO 8601",
        "reason": "string" | null,
        "error": "string" | null,
        "t80_value": number | null
      }
    }
  ]
}
```

#### Forecast Metadata Methods
- `SEMI_AUTOMATED_BATCH_FORECAST`: Batch forecasting
- `Simple_Trend_Fallback_After_Error`: Fallback linear trend
- `Log_ARIMA_Grid_Search`: ARIMA-based forecasting
- `V3_Disruptor_Exponential`: Exponential growth model

### 5. Final Response (`response`)

**Field:** `final_response`
**Type:** string (HTML)
**Description:** Main answer to user query with inline citations

```json
{
  "final_response": "<b>Lead demand in China is projected to peak around 2025.</b> This projection is inferred from global lead demand trends peaking at 12,259 kt in 2024 before declining, as per Lead_Annual_Implied_Demand_Global[1]..."
}
```

### 6. Analysis Sections

All analysis sections are HTML-formatted strings supporting tables, lists, and styling.

#### Mathematical Analysis

**Field:** `mathematical_analysis`
**Type:** string (HTML)
**Description:** Step-by-step mathematical analysis with tables and formulas

```json
{
  "metadata": {
    "mathematical_analysis": "<h3>Mathematical Analysis</h3>\n<p>This analysis evaluates...</p>\n<table>...</table>"
  }
}
```

#### Technology Convergence

**Field:** `technological_convergence`
**Type:** string (HTML)
**Description:** Analysis of converging technologies and disruption points

```json
{
  "metadata": {
    "technological_convergence": "<h3>Technology Convergence Analysis</h3>\n<p>Technology convergence refers to...</p>"
  }
}
```

#### Market Transformation

**Field:** `market_transformation`
**Type:** string (HTML)
**Description:** Market disruption models and forecast scenarios

```json
{
  "metadata": {
    "market_transformation": "<h3>Market Transformation Analysis</h3>\n<p>In the context of lead demand peaking...</p>"
  }
}
```

#### Strategic Implications

**Field:** `strategic_implications`
**Type:** string (HTML)
**Description:** Step-by-step execution analysis with business implications

```json
{
  "metadata": {
    "strategic_implications": "### Step Execution\n\n#### Step 1: Analyze global lead demand...\n<h3>Hypothesis: Strategic Implications...</h3>"
  }
}
```

### 7. News Articles (`news_article_response`)

**Field:** `news_article_response`
**Type:** object[]
**Description:** Related news articles with metadata

```json
{
  "metadata": {
    "news_article_response": [
      {
        "title": "string",
        "text": "string",
        "authors": ["string"],
        "publish_date": "ISO 8601" | null,
        "top_image": "URL" | null,
        "movies": [],
        "url": "URL"
      }
    ]
  }
}
```

### 8. References (`references`)

**Field:** `references`
**Type:** string (HTML)
**Description:** Formatted list of all datasets used with full metadata

```html
[1] Total annual implied lead demand globally<br>
[2] Annual implied lead demand for non-battery uses globally<br>
<hr><br>
<h3 id='ref-dataset-1'> [1] Total annual implied lead demand globally </h3>
<ul>
  <li>dataset_name: Lead_Annual_Implied_Demand_Global</li>
  <li>description: Total annual implied lead demand globally</li>
  <li>type: adoption</li>
  ...
</ul>
```

### 9. Follow-up Response (`follow-up-response`)

**Field:** `response`
**Type:** string (HTML)
**Description:** Short answer to follow-up questions with dataset links

```json
{
  "response": "Global lead demand is forecasted to peak in 2024 at 12,259 kt, based on the <a href='#ref-dataset-1'>Lead_Annual_Implied_Demand_Global</a> dataset..."
}
```

### 10. History (`history`)

**Field:** `history`
**Type:** array
**Description:** Conversation history (typically empty in polling stage)

```json
{
  "history": []
}
```

## Example Complete Flow

### Step 1: Initial Query (Polling)
```json
{
  "flow_run_id": "UUID",
  "chat_id": "chat_ID",
  "stage": "polling",
  "chat_type": "compass",
  "next_flow": null,
  "artifacts": ["action-plan"],
  "timestamp": "2025-10-28T12:43:49.034043+05:30",
  "is_acknowledged": false,
  "action_plan": ["Step 1", "Step 2", ...]
}
```

### Step 2: Research Ready (Knowledge Graph)
```json
{
  "flow_run_id": "UUID",
  "chat_id": "chat_ID",
  "stage": "ready_for_research",
  "chat_type": "compass",
  "next_flow": null,
  "artifacts": ["knowledge_graph"],
  "timestamp": "2025-10-28T12:43:49.836609+05:30",
  "is_acknowledged": false,
  "knowledge_graph": {
    "nodes": [...],
    "relationships": [...]
  }
}
```

### Step 3: Research Ready (Query Understanding)
```json
{
  "flow_run_id": "UUID",
  "chat_id": "chat_ID",
  "stage": "ready_for_research",
  "chat_type": "compass",
  "next_flow": null,
  "artifacts": ["query-understanding"],
  "timestamp": "2025-10-28T12:43:51.170380+05:30",
  "is_acknowledged": false,
  "detailed_plan": "# Disruption Analysis Plan...",
  "confirmation_query": "Does this proposed analysis plan align...",
  "datasets": [...],
  "missing_datasets": [...]
}
```

### Step 4: Data Collection (Forecast Data)
```json
{
  "flow_run_id": "UUID",
  "chat_id": "chat_ID",
  "stage": "polling",
  "chat_type": "compass",
  "next_flow": "stellar_generic_follow_up",
  "artifacts": ["forecast-data", "knowledge-graph"],
  "timestamp": "2025-10-28T12:44:03.217663+05:30",
  "is_acknowledged": false,
  "forecast_data": [...]
}
```

### Step 5: Final Response
```json
{
  "flow_run_id": "UUID",
  "chat_id": "chat_ID",
  "stage": "completed",
  "chat_type": "compass",
  "next_flow": "stellar_generic_follow_up",
  "artifacts": ["response"],
  "timestamp": "2025-10-28T12:44:03.852115+05:30",
  "is_acknowledged": false,
  "final_response": "<b>Lead demand in China...</b>",
  "metadata": {
    "mathematical_analysis": "...",
    "technological_convergence": "...",
    "market_transformation": "...",
    "strategic_implications": "...",
    "news_article_response": [...],
    "references": "..."
  }
}
```

## Data Type Reference

### Entity Types
- **disruptor**: New technology displacing incumbents (e.g., EV, solar)
- **incumbent**: Legacy technology being displaced (e.g., ICE, coal)
- **chimera**: Bridge technology (e.g., PHEV)

### Regions
- **China**
- **USA**
- **Europe**
- **Rest_of_World**
- **Global** (aggregated)

### Dataset Types
- **adoption**: Annual sales, demand, or capacity data
- **cost**: Cost curve data (LCOE, $/mile, $/kWh)

### Units
- **kt**: Kilotons (1,000 metric tons)
- **vehicles/year**: Annual vehicle sales
- **units/year**: Annual unit sales (e.g., forklifts)
- **$/KWh**: Dollars per kilowatt-hour
- **$/MWh**: Dollars per megawatt-hour
- **GW**: Gigawatts (capacity)
- **TWh**: Terawatt-hours (generation)

## Message Flow Sequence

1. **User submits query** → `role: "user"`, plain text content
2. **System polls** → `stage: "polling"`, `artifacts: ["action-plan"]`
3. **System builds knowledge graph** → `stage: "ready_for_research"`, `artifacts: ["knowledge_graph"]`
4. **System creates analysis plan** → `stage: "ready_for_research"`, `artifacts: ["query-understanding"]`
5. **System gathers forecast data** → `stage: "polling"`, `artifacts: ["forecast-data"]`
6. **System completes analysis** → `stage: "completed"`, `artifacts: ["response"]`
7. **Follow-up queries** → `stage: "completed"`, `artifacts: ["follow-up-response"]`

## Notes

- All assistant message `content` fields are **stringified JSON** and must be parsed before use
- Timestamps use ISO 8601 format with timezone offset (e.g., `+05:30` for IST)
- HTML content in analysis fields supports tables, lists, headers, and inline styles
- Dataset references use bracket notation `[1]`, `[2]` linked to `#ref-dataset-N` anchors
- Flow IDs change between query sessions but chat_id remains constant per conversation
