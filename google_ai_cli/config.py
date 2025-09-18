# config.py
"""
Configuration constants for the Google AI CLI tool.

This file centralizes all paths and selectors for easy maintenance.
"""
from pathlib import Path

# --- Paths (relative to the project root) ---
# This directory will be created where you run the script.
# It holds the browser profile (for login sessions) and prompt history.
SESSION_DIR = Path("./google_ai_session")
USER_DATA_DIR = SESSION_DIR / "profile"
PROMPT_HISTORY_FILE = SESSION_DIR / "prompt_history.txt"

# --- URL ---
GOOGLE_SEARCH_URL = "https://google.com/search?q={query}&udm=50"

# --- Robust Selectors ---
RESPONSE_CONTAINER_SELECTOR = 'div[data-subtree="aimc"]'
NEW_CHAT_BUTTON_SELECTOR = 'button[aria-label="Start new search"]'
INPUT_TEXTAREA_SELECTOR = 'textarea[placeholder="Ask anything"]'

# --- Content Selectors (inside the response container) ---
HEADING_SELECTOR = '.otQkpb'
PARAGRAPH_SELECTOR = '.Y3BBE'
LIST_SELECTOR = '.U6u95'