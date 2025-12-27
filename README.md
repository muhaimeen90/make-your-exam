# makeyourexam

A powerful tool to forge exams from PDF documents using AI.

## Quick Start

1.  **Clone the repository**
2.  **Setup Environment**:
    ```bash
    cp .env.example .env
    # Add your GEMINI_API_KEY to .env
    ```
3.  **Run the App**:
    ```bash
    ./run_app.sh
    ```
    This script handles both backend and frontend startup.

## Structure
-   `frontend/`: React + Vite application (Memphis design style)
-   `backend/`: Python FastAPI server
