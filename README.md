# Google AI Research Agent

This project contains a command-line interface (`google_ai_cli.py`) to interact with Google's AI search mode and a sophisticated, autonomous research agent (`research_agent.py`) that uses the CLI as a tool.

The agent leverages a local, OpenAI-compatible AI model to perform iterative searches, gather information, and compile a final, detailed report.

## Features

- **Autonomous Research:** Provide a topic, and the agent will formulate search queries and execute them.
- **Function Calling:** Uses a local AI model's function calling feature to interact with the real world via the `google_ai_cli.py` tool.
- **Iterative Deep Dives:** The agent analyzes search results and decides whether to dig deeper with more specific queries.
- **Structured Reporting:** Generates a final report with a TL;DR summary and a detailed findings section.
- **Robust and Verbose:** Includes extensive logging and error handling for reliability and debugging.

## Prerequisites

1.  **Python 3.8+**
2.  **An OpenAI-compatible local AI server** running and accessible (e.g., at `http://localhost:2048`).
3.  **A browser** (like Chrome or Firefox) for Playwright to control.

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repo-url>
    cd AIModeProxy
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    The agent requires the `openai` library. The existing dependencies are in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    pip install openai
    ```

4.  **Install Playwright browsers:**
    The first time you run the CLI, it may prompt you, or you can do it manually.
    ```bash
    playwright install
    ```

## How to Run the Research Agent

1.  **Ensure your local AI server is running.** The agent is configured by default to connect to `http://localhost:2048`.

2.  **Run the `research_agent.py` script from the project's root directory (`AIModeProxy/`).**

    Provide the research topic as a command-line argument.

    **Basic Usage:**
    ```bash
    python research_agent.py "The history and impact of the ARM architecture on mobile computing"
    ```

    **Example with more iterations:**
    ```bash
    python research_agent.py "Compare and contrast the python libraries requests and httpx" --iterations 7
    ```

    **Run with debug logging:**
    For highly verbose output, use the `--debug` flag. All logs are also saved to `research_agent.log`.
    ```bash
    python research_agent.py "latest advancements in solid-state battery technology" --debug
    ```

3.  **Monitor the Process:**
    The agent will print its current status to the console, showing you which iteration it's on and what it's searching for.

    ```
    [STATUS] Research Iteration 1/5...
    [SEARCHING] AI is searching for: "history of ARM architecture"

    [STATUS] Research Iteration 2/5...
    [SEARCHING] AI is searching for: "ARM architecture impact on smartphones"
    ...
    ```

4.  **Get the Final Report:**
    Once the research is complete, the final, formatted report will be printed to the console.