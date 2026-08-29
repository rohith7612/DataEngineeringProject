# InsightEngine: Enterprise AI Data Agent

## 🏗 Project Architecture
The **InsightEngine** is an enterprise-grade, self-healing agentic system that translates natural language into verified SQL, real-time visualizations, and executive-ready reporting. It leverages **GPT-4o-mini** to translate business inquiries into safe PostgreSQL queries and provides executive-style insights.

---

## 📄 File-by-File Explanation
### 1. `agent.py` (The Core Intelligence)
This is the heart of the application. It handles the logic for SQL generation, security filtering, and AI summarization.

*   **`QueryResult` (Class):** A wrapper for database results. It is "lazy," meaning it only converts data into a pandas DataFrame when specifically needed, saving memory.
*   **`ThreadSafeLRUCache` (Class):** A custom caching mechanism. It stores previously generated SQL queries and AI explanations so that if the same question is asked twice, the answer is returned instantly without calling the LLM or re-running the query.
*   **`execute_query(query)`:** 
    *   **Purpose:** Runs SQL against the database.
    *   **Security:** Includes a strict filter that only allows `SELECT` and other read-only operations. It blocks any attempt to `DROP`, `DELETE`, or `UPDATE` tables.
*   **`get_region_summary()`:** 
    *   **Purpose:** Fetches all data from the `gold_region_sales` table and asks the AI to provide a high-level executive summary of regional performance.
*   **`generate_sql(question)`:** 
    *   **Purpose:** Uses GPT-4o-mini to convert a user's natural language question (e.g., "Which region is most profitable?") into a valid PostgreSQL query.
    *   **Logic:** It injects the database schema (from `schema.py`) into the prompt so the AI knows exactly which tables and columns to use.
*   **`explain_results(question, data)`:** 
    *   **Purpose:** Takes the raw numbers returned by the database and uses the AI to write a concise, human-readable summary for the CEO.
*   **`answer_question(question)`:** 
    *   **Purpose:** The main orchestrator. It calls `generate_sql`, then `execute_query`, and finally `explain_results` to provide a complete answer.

---

## 2. `db.py` (Database Connectivity)
Handles the "plumbing" between the Python code and the PostgreSQL database.

*   **Connection Pooling:** Configures a "pool" of 10-20 connections. This is an optimization that prevents the app from having to log into the database every single time a query is run, significantly improving speed.
*   **URL Encoding:** Safely handles database passwords that might contain special characters (like `@` or `!`).
*   **Health Check:** Contains a small script at the bottom to verify the connection is active.

---

## 3. `app.py` (Backend API)
A **FastAPI** server that allows other applications or services to communicate with the Analytics Agent.

*   **`add_process_time_header`:** A middleware function that measures exactly how many milliseconds every request takes and adds it to the response header for performance monitoring.
*   **`@app.get("/")`:** A health check endpoint to verify the API is online.
*   **`@app.get("/summary")`:** Triggers the automated regional performance summary.
*   **`@app.post("/ask")`:** The primary endpoint where external apps send a JSON question and receive a SQL/Summary response.

---

## 4. `chat_app.py` (Frontend User Interface)
A **Streamlit** dashboard that provides a premium, user-friendly chat interface for the CEO.

*   **Custom Styling:** Uses CSS to inject a "Modern Dark Mode" aesthetic with Jakarta Sans typography and gradient headers.
*   **Session Management:** Keeps track of the chat history so the user can see their previous questions and answers during the session.
*   **Sidebar:** Provides transparency by allowing the user to inspect the database schema being used by the AI.

---

## 5. `mcp_server.py` (Model Context Protocol)
Implements the new **Model Context Protocol (MCP)** by Anthropic.

*   **Purpose:** This allows the agent to be used as a "tool" by other AI models (like Claude or ChatGPT).
*   **`run_sql` / `get_region_sales` / `get_top_products`:** These are "exposed tools" that an AI can autonomously call to fetch data without human intervention.

---

## 6. `schema.py` (Knowledge Base)
A simple but critical file containing the definition of the database tables. This is the "map" that the AI uses to understand where data lives.

---

## 🚀 Key Optimizations Implemented
1.  **Self-Healing SQL Engine:** If the AI generates a query that causes a database error (e.g., incorrect syntax or column name), the agent automatically catches the error, sends it back to the AI for analysis, and retries with a corrected query. This happens seamlessly before the user sees any error.
2.  **Dual-Layer Caching:** Both SQL generation and Explanation generation are cached to minimize API costs and latency.
3.  **Thread Safety:** The cache and database connections are designed to handle multiple users simultaneously without crashing.
4.  **Security Filtering:** A regex-based SQL guard ensures the AI can never accidentally (or intentionally) modify or delete business data.
5.  **Lazy Loading:** Data is only processed into heavy objects (like DataFrames) when absolutely necessary, keeping the app lightweight.
