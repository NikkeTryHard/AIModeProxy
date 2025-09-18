# ai_controller.py
"""
Contains the GoogleAIController class for browser automation and response parsing.
"""
import logging
import re
import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from config import (
    RESPONSE_CONTAINER_SELECTOR,
    NEW_CHAT_BUTTON_SELECTOR,
    INPUT_TEXTAREA_SELECTOR,
    HEADING_SELECTOR,
    PARAGRAPH_SELECTOR,
    LIST_SELECTOR
)

class GoogleAIController:
    """Handles interactions with an already-opened Google AI page."""

    def __init__(self, page: Page):
        self.page = page

    def wait_for_response_stabilization(self):
        """Waits for the text content of the last response to stop growing."""
        logging.info("Waiting for response to finish streaming...")
        try:
            latest_response = self.page.locator(RESPONSE_CONTAINER_SELECTOR).last
            latest_response.scroll_into_view_if_needed(timeout=5000)
            
            last_len = 0
            stable_checks = 0
            max_stable_checks = 6  # Requires 3 seconds of no growth (6 checks * 0.5s)

            for i in range(240):  # Max wait of 120 seconds
                current_text = latest_response.inner_text(timeout=5000)
                current_len = len(current_text)
                logging.debug("Stabilization check %d: length=%d, last_len=%d, stable_checks=%d",
                              i + 1, current_len, last_len, stable_checks)

                if current_len > 0 and current_len == last_len:
                    stable_checks += 1
                    if stable_checks >= max_stable_checks:
                        logging.info("Response content stabilized after %.1f seconds.", i * 0.5)
                        return
                else:
                    stable_checks = 0
                last_len = current_len
                time.sleep(0.5)
            
            logging.warning("Wait for stabilization timed out. Response may be incomplete.")
        except PlaywrightTimeoutError:
            logging.error("Could not find response container during stabilization check.")
            raise

    def _parse_element_to_markdown(self, element) -> str:
        """Recursively parses a BeautifulSoup element into a Markdown string."""
        content = ''
        for child in element.contents:
            if isinstance(child, NavigableString):
                content += str(child)
            elif isinstance(child, Tag):
                if child.name in ['b', 'strong']:
                    content += f"**{child.get_text(strip=True)}**"
                elif child.name in ['i', 'em']:
                    content += f"*{child.get_text(strip=True)}*"
                elif child.name == 'a':
                    href = child.get('href', '')
                    content += f"[{child.get_text(strip=True)}]({href})"
                else:
                    content += self._parse_element_to_markdown(child)
        return content

    def extract_response_as_markdown(self) -> str:
        """Extracts the last AI response and converts its HTML to Markdown."""
        try:
            logging.info("Extracting and parsing the latest response...")
            container = self.page.locator(RESPONSE_CONTAINER_SELECTOR).last
            html_content = container.inner_html()
            
            # Clean out Google's internal markers before parsing
            cleaned_html = re.sub(r'Sv6Kpe\[.*?\]', '', html_content)
            
            soup = BeautifulSoup(cleaned_html, 'lxml')
            markdown_output = []

            for element in soup.select(f"{HEADING_SELECTOR}, {PARAGRAPH_SELECTOR}, {LIST_SELECTOR}"):
                class_attrs = element.get('class', [])
                
                if HEADING_SELECTOR.strip('.') in class_attrs:
                    markdown_output.append(f"\n### {element.get_text(strip=True)}\n")
                elif PARAGRAPH_SELECTOR.strip('.') in class_attrs:
                    parsed_text = self._parse_element_to_markdown(element).strip()
                    markdown_output.append(parsed_text)
                elif LIST_SELECTOR.strip('.') in class_attrs:
                    for li in element.find_all('li', recursive=False):
                        item_text = self._parse_element_to_markdown(li).strip()
                        markdown_output.append(f"* {item_text}")
                    markdown_output.append("")
            
            parsed_response = "\n".join(markdown_output).strip()
            if not parsed_response:
                logging.warning("Markdown parsing resulted in empty content. Falling back to plain text.")
                return container.inner_text()

            logging.info("Parsing successful.")
            return parsed_response
        except Exception as e:
            logging.error("Failed to parse response HTML: %s. Falling back to plain text.", e)
            try:
                return self.page.locator(RESPONSE_CONTAINER_SELECTOR).last.inner_text()
            except Exception as fallback_e:
                logging.error("Fallback text extraction also failed: %s", fallback_e)
                return "Error: Could not extract response."

    def new_chat(self) -> str:
        """Clicks the 'New Chat' button to start a new session."""
        try:
            self.page.click(NEW_CHAT_BUTTON_SELECTOR, timeout=10000)
            self.page.wait_for_selector(INPUT_TEXTAREA_SELECTOR, state="visible", timeout=10000)
            logging.info("Started a new chat session.")
            return "New chat started successfully."
        except PlaywrightTimeoutError:
            return "Error: Timed out trying to start a new chat."