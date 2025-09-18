# config.py
"""Configuration constants for the Google AI CLI tool."""

from pathlib import Path

# --- URL and Session ---
GOOGLE_SEARCH_URL = "https://google.com/search?q={query}&udm=50"
USER_DATA_DIR = Path.home() / ".google_ai_cli"
PROMPT_HISTORY_FILE = USER_DATA_DIR / "prompt_history.txt"

# --- Robust Selectors ---
RESPONSE_CONTAINER_SELECTOR = 'div[data-subtree="aimc"]'
NEW_CHAT_BUTTON_SELECTOR = 'button[aria-label="Start new search"]'
INPUT_TEXTAREA_SELECTOR = 'textarea[placeholder="Ask anything"]'
HEADING_SELECTOR = '.otQkpb'
PARAGRAPH_SELECTOR = '.Y3BBE'
LIST_SELECTOR = '.U6u95'