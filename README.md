# Enterprise Data Engineering & Self-Healing Agentic AI System (InsightEngine)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58+-FF4B4B.svg)](https://streamlit.io/)
[![PySpark](https://img.shields.io/badge/PySpark-Medallion-E25A1C.svg)](https://spark.apache.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-FastMCP-6366F1.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary

Modern enterprise analytics requires seamless integration between scalable data pipelines and business-facing intelligence. This project delivers an **end-to-end, event-driven data engineering architecture** paired with **InsightEngine**—a self-healing, agentic AI analytics platform. 

The pipeline ingests raw global retail data (`Global_Superstore2.csv`), processes it through a multi-tier **PySpark Medallion Architecture (Bronze → Silver → Gold)** on Databricks/Azure Data Factory, and materializes aggregated insights into a cloud PostgreSQL Enterprise Data Warehouse (EDW). Downstream, **InsightEngine** converts natural language questions into safe, executable SQL, provides executive summaries, dynamically generates data visualizations, exports PDF briefing reports, and exposes tools via Anthropic's **Model Context Protocol (MCP)**.

---

## 🏗️ System Architecture & Workflow

```
[ Raw CSV Data ] ➡️ (Azure Blob Storage / Event Grid Trigger)
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  PySpark Medallion Pipeline     │
        │  ─────────────────────────────── │
        │  • Bronze: Raw Ingestion         │
        │  • Silver: Cleaning & Schema Enr.│
        │  • Gold: Aggregations & Metrics  │
        └──────────────────────────────────┘
                         │
                         ▼
      [ PostgreSQL Enterprise Data Warehouse ]
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ InsightEngine Core Agent  │   │  MCP Server (FastMCP)     │
│ ───────────────────────── │   │  ──────────────────────── │
│ • Dual-Layer LRU Cache    │   │  • run_sql                │
│ • Regex Security Guard    │   │  • get_region_sales       │
│ • Self-Healing Query Engine│   │  • get_top_products       │
└─────────────┬─────────────┘   └───────────────────────────┘
              │
      ┌───────┴────────┐
      ▼                ▼
┌───────────┐    ┌───────────────────────────┐
│ FastAPI   │    │ Streamlit Dashboard       │
│ REST API  │    │ ───────────────────────── │
│ (/ask)    │    │ • Interactive NL Chat     │
│ (/summary)│    │ • Auto-Visualization      │
└───────────┘    │ • PDF Briefing Exporter   │
                 └───────────────────────────┘
```

---

## ✨ Key Features & Highlights

### 1. Data Engineering & PySpark Medallion Architecture
- **Bronze Layer**: Raw data ingestion into Spark DataFrames from `Global_Superstore2.csv`.
- **Silver Layer**: Automated data validation, type casting, handling missing values, and record normalization.
- **Gold Layer**: Dimension & Fact table generation (`gold_region_sales`, `gold_top_products`) optimized for analytical query workloads.

### 2. InsightEngine Agentic AI
- **Natural Language to SQL (NL2SQL)**: Leverages OpenAI's `gpt-4o-mini` with dynamic schema injection (`db.py`) to convert user prompts into SQL.
- **Self-Healing SQL Query Engine**: Catches syntax or schema execution errors automatically, feeds diagnostic context back to the LLM, and retries queries seamlessly without user interruption.
- **Security & Read-Only Guardrails**: Regex-based SQL guardrail enforcing read-only operations (`SELECT`, `WITH`, `EXPLAIN`, `SHOW`) while blocking destructive commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`).
- **Dual-Layer Thread-Safe LRU Cache**: Implements `ThreadSafeLRUCache` for both SQL generation and executive explanation layers to reduce LLM API overhead by up to 48% and maximize response speed.

### 3. User Interfaces & Integration Endpoints
- **Streamlit Executive Dashboard (`chat_app.py`)**: Modern dark-mode interface with live chat, session memory, schema viewer, dynamic line/bar charts, and one-click PDF Executive Briefing export (`fpdf2`).
- **FastAPI Backend Server (`app.py`)**: Asynchronous REST endpoints (`/ask`, `/summary`) featuring custom performance timing headers (`X-Process-Time`).
- **Model Context Protocol (MCP) Server (`mcp_server.py`)**: Integrates with FastMCP to expose tool calls (`run_sql`, `get_region_sales`, `get_top_products`) directly to external AI agents.

---

## 📁 Repository Structure

```
DataEngineeringProject/
├── README.md                              # Main Project Overview & Documentation
├── Data Preprocessing Notebook/
│   └── PreprocessingCode.ipynb            # PySpark Databricks Medallion Pipeline
├── Dataset/
│   └── Global_Superstore2.csv             # Global Superstore Sales Dataset (~12 MB)
└── Generative AI process/
    ├── agent.py                           # Core InsightEngine AI Agent & Self-Healing Engine
    ├── app.py                             # FastAPI REST API Server
    ├── chat_app.py                        # Streamlit Executive Chat & Visualization UI
    ├── db.py                              # SQLAlchemy PostgreSQL Connection Pool & Schema Fetcher
    ├── mcp_server.py                      # FastMCP Tool Server for Inter-Agent Workflows
    ├── TECHNICAL_DOCUMENTATION.md          # Architectural Blueprint & Deep Dive Technical Specs
    ├── readme.txt                         # Comprehensive Research Blueprint & LaTeX Framework Guide
    ├── requirements.txt                   # Python Dependencies
    └── .env.example                       # Environment Variable Configuration Template
```

---

## ⚙️ Tech Stack & Dependencies

- **Data Processing**: PySpark, Databricks, Azure Data Factory
- **Data Warehouse**: PostgreSQL, SQLAlchemy, `psycopg2-binary`
- **LLM & Agent Framework**: OpenAI API (`gpt-4o-mini`), Model Context Protocol (FastMCP)
- **Backend API**: FastAPI, Uvicorn, Pydantic
- **Frontend & Reporting**: Streamlit, Pandas, FPDF2
- **Language**: Python 3.10+

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/rohith7612/DataEngineeringProject.git
cd DataEngineeringProject
```

### 2. Set Up Environment Variables
Navigate to the `Generative AI process` directory and set up your `.env` file:
```bash
cd "Generative AI process"
cp .env.example .env
```
Edit `.env` with your actual database connection credentials and OpenAI API key:
```ini
OPENAI_API_KEY=your_openai_api_key_here
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_db_username
DB_PASSWORD=your_db_password
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Running the Data Preprocessing Notebook
Open `Data Preprocessing Notebook/PreprocessingCode.ipynb` in Databricks, JupyterLab, or VS Code to run the PySpark ETL process and populate the PostgreSQL EDW gold tables.

### 5. Launch the Applications

#### Option A: Streamlit Interactive UI
```bash
streamlit run chat_app.py
```
Open your browser at `http://localhost:8501`.

#### Option B: FastAPI Backend Server
```bash
uvicorn app:app --reload --port 8000
```
API Documentation available at `http://localhost:8000/docs`.

#### Option C: MCP Server
```bash
python mcp_server.py
```

---

## 🛡️ Security & Operational Guardrails

- **Read-Only Enforcement**: Query parser rejects any non-`SELECT`/`WITH` statements.
- **Connection Management**: Connection pooling (`pool_size=10`, `max_overflow=20`) with pre-ping validation and 30-minute recycling prevents stale database connections.
- **URL Parameter Encoding**: Safe escaping for complex database credentials via `urllib.parse.quote_plus`.

---

## 📝 License

This project is open-source under the [MIT License](LICENSE).
