#!/usr/bin/env python
# google_ai_cli.py
"""
A command-line interface to control Google's AI search mode.
"""
import argparse
import logging
import sys
import os
from datetime import datetime
from urllib.parse import quote_plus

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from camoufox.sync_api import Camoufox

from ai_controller import GoogleAIController
from config import (
    GOOGLE_SEARCH_URL,
    USER_DATA_DIR,
    PROMPT_HISTORY_FILE,
    SESSION_DIR,
    RESPONSE_CONTAINER_SELECTOR,
    NEW_CHAT_BUTTON_SELECTOR,
    INPUT_TEXTAREA_SELECTOR
)

def save_conversation(prompt: str, response: str):
    """Appends the prompt and response to the history file."""
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(PROMPT_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- Prompt sent at {timestamp} ---\n")
            f.write(f"{prompt}\n\n")
            f.write(f"--- Response ---\n")
            f.write(f"{response}\n")
            f.write("="*40 + "\n\n")
        logging.info("Conversation saved to %s", PROMPT_HISTORY_FILE)
    except IOError as e:
        logging.error("Could not write to history file: %s", e)

def handle_initial_popups(page: Page):
    """Handles cookie banners or other initial dialogs."""
    try:
        accept_button = page.locator('button:has-text("Accept all")')
        if accept_button.is_visible(timeout=5000):
            accept_button.click()
            logging.info("Accepted cookie policy.")
    except PlaywrightTimeoutError:
        logging.info("No cookie banner found.")

def main():
    """Main function to parse arguments and run the controller."""
    parser = argparse.ArgumentParser(
        description="Control Google AI from the command line.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("command", choices=["prompt", "new"], help="The command to execute.")
    parser.add_argument("text", nargs="?", default="", help="The prompt text to send.")
    parser.add_argument("--headful", action="store_true", help="Run in a visible browser window.")
    parser.add_argument("--save", action="store_true", help="Save the prompt and response to a history file.")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging.")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    if args.command == "prompt" and not args.text:
        parser.error("The 'prompt' command requires a text argument.")

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    logging.info("Using profile directory: %s", USER_DATA_DIR)

    try:
        with Camoufox(
            headless=not args.headful,
            persistent_context=True,
            user_data_dir=str(USER_DATA_DIR),
            humanize=True
        ) as browser:
            page = browser.new_page()
            controller = GoogleAIController(page)
            
            if args.command == "prompt":
                encoded_prompt = quote_plus(args.text)
                url = GOOGLE_SEARCH_URL.format(query=encoded_prompt)
                logging.info("Navigating to: %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                handle_initial_popups(page)
                
                logging.info("Waiting for AI response container to appear (max 90s)...")
                if args.headful:
                    logging.info("If a CAPTCHA appears, please solve it in the browser window.")
                
                page.wait_for_selector(RESPONSE_CONTAINER_SELECTOR, state="visible", timeout=90000)
                logging.info("Response container found.")
                
                controller.wait_for_response_stabilization()
                response = controller.extract_response_as_markdown()
                print(response)

                if args.save:
                    save_conversation(args.text, response)

            elif args.command == "new":
                url = GOOGLE_SEARCH_URL.format(query="start new chat")
                logging.info("Navigating to default page to start new chat...")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                handle_initial_popups(page)
                
                logging.info("Waiting for UI to load (max 90s)...")
                page.wait_for_selector(NEW_CHAT_BUTTON_SELECTOR, state="visible", timeout=90000)
                
                message = controller.new_chat()
                print(message)

    except PlaywrightTimeoutError:
        logging.error("Operation timed out. This could be due to a CAPTCHA, slow network, or a page structure change.")
        sys.exit(1)
    except Exception as e:
        logging.error("A critical error occurred: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()