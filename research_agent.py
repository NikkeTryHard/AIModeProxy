#!/usr/bin/env python
# research_agent.py
"""
An autonomous research agent that uses a local AI model with function calling
to perform iterative web searches and generate a detailed report.
"""
import argparse
import json
import logging
import subprocess
import sys
from typing import Dict, Any

# Use the official OpenAI library to connect to the compatible API
import openai

# --- Configuration ---
# Your local AI server details
OPENAI_API_BASE = "http://localhost:2048/v1"  # Standard for local servers
OPENAI_API_KEY = "123456"  # The provided API key
MODEL_NAME = "gemini-2.5-pro" # The provided model name

# Path to the Google AI CLI tool
GOOGLE_AI_CLI_PATH = "google_ai_cli/google_ai_cli.py"

# --- Tool Definition ---
def search_google(query: str) -> str:
    """
    Performs a search using the Google AI mode and returns the results.
    Use this to find information, answer questions, and get details on any topic.
    Formulate a clear, specific question or search term for the best results.

    Args:
        query (str): The search query or question.

    Returns:
        str: The search results from Google's AI mode, or an error message.
    """
    logging.info("Executing search tool with query: '%s'", query)
    try:
        # Use sys.executable to ensure we're using the same python env
        command = [sys.executable, GOOGLE_AI_CLI_PATH, "prompt", query]

        # Execute the command as a subprocess
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,  # Raise an exception for non-zero exit codes
            timeout=180 # 3-minute timeout for the search call
        )

        logging.debug("Search tool raw stdout:\n%s", process.stdout)
        if process.stderr:
            logging.warning("Search tool raw stderr:\n%s", process.stderr)

        return process.stdout.strip()

    except FileNotFoundError:
        error_msg = f"Error: The script '{GOOGLE_AI_CLI_PATH}' was not found."
        logging.error(error_msg)
        return error_msg
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Error: The search script failed with exit code {e.returncode}.\n"
            f"Stderr: {e.stderr.strip()}"
        )
        logging.error(error_msg)
        return error_msg
    except subprocess.TimeoutExpired:
        error_msg = "Error: The search script timed out after 180 seconds."
        logging.error(error_msg)
        return error_msg


class ResearchAgent:
    """
    Orchestrates the research process by managing interaction with the AI model
    and executing tools.
    """
    def __init__(self, model: str, api_base: str, api_key: str):
        self.model = model
        self.client = openai.OpenAI(base_url=api_base, api_key=api_key)
        self.conversation_history = []
        self.research_data = [] # Stores (query, result) tuples
        self.tool_map = {"search_google": search_google}
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_google",
                    "description": (
                        "Searches Google using its AI mode to find information "
                        "on a given topic or question."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The specific search query or question.",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    def _call_ai(self, messages: list, use_tools: bool = True) -> Dict[str, Any]:
        """A wrapper for making calls to the OpenAI compatible API."""
        logging.debug("Sending messages to AI: %s", json.dumps(messages, indent=2))
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if use_tools else None,
                tool_choice="auto" if use_tools else None,
            )
            return response.choices[0].message
        except openai.APIConnectionError as e:
            logging.error("Failed to connect to the AI server at %s. Is it running?", self.client.base_url)
            raise e
        except openai.APIStatusError as e:
            logging.error("Received an error from the AI API: %s", e)
            raise e


    def run(self, topic: str, max_iterations: int = 5) -> str:
        """
        Starts and manages the research process for a given topic.

        Args:
            topic (str): The initial research topic.
            max_iterations (int): The maximum number of search cycles to perform.

        Returns:
            str: The final, formatted research report.
        """
        logging.info("--- Starting New Research Task ---")
        logging.info("Topic: %s", topic)
        logging.info("Max Iterations: %d", max_iterations)

        system_prompt = (
            "You are an expert research assistant. Your goal is to gather "
            "comprehensive information about the user's topic. "
            "Think step-by-step. First, formulate a search query to start. "
            "Then, use the `search_google` tool to find information. "
            "Analyze the results, and decide if you need more information. "
            "If so, formulate a new, more specific query to dig deeper or explore a new angle. "
            "When you are confident you have enough information to write a detailed report, "
            "respond with the final message 'RESEARCH_COMPLETE' and nothing else."
        )
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please research the following topic: {topic}"}
        ]

        for i in range(max_iterations):
            logging.info("--- Research Iteration %d/%d ---", i + 1, max_iterations)
            print(f"\n[STATUS] Research Iteration {i + 1}/{max_iterations}...")

            ai_response = self._call_ai(self.conversation_history)
            self.conversation_history.append(ai_response.model_dump())

            if ai_response.tool_calls:
                logging.info("AI decided to use a tool.")
                for tool_call in ai_response.tool_calls:
                    self._execute_tool_call(tool_call)
            elif "RESEARCH_COMPLETE" in (ai_response.content or ""):
                logging.info("AI signaled research is complete.")
                print("[STATUS] Research phase complete. Generating final report...")
                return self._generate_final_report()
            else:
                logging.warning("AI did not use a tool or signal completion. Ending research.")
                print("[STATUS] AI provided a response without searching. Generating report from available data...")
                return self._generate_final_report()

        logging.warning("Reached max iterations. Moving to report generation.")
        print("\n[STATUS] Reached max search iterations. Generating final report...")
        return self._generate_final_report()

    def _execute_tool_call(self, tool_call: Dict[str, Any]):
        """Executes a tool call requested by the AI and appends the result to history."""
        func_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
            query = args.get("query")
            logging.info("AI wants to call '%s' with query: '%s'", func_name, query)
            print(f"[SEARCHING] AI is searching for: \"{query}\"")

            if func_name in self.tool_map:
                tool_function = self.tool_map[func_name]
                result = tool_function(query=query)
                self.research_data.append({"query": query, "result": result})
            else:
                logging.error("AI tried to call unknown function: %s", func_name)
                result = f"Error: Unknown tool '{func_name}'."

            logging.debug("Appending tool result to conversation history.")
            self.conversation_history.append(
                {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": result}
            )
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON arguments from AI: %s", tool_call.function.arguments)
            self.conversation_history.append(
                {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": "Error: Invalid arguments format."}
            )

    def _generate_final_report(self) -> str:
        """
        Generates the final report by synthesizing all collected research data.
        """
        if not self.research_data:
            return "No research was conducted. Could not generate a report."

        logging.info("Generating final report from %d research entries.", len(self.research_data))

        report_prompt = (
            "You are a report writing expert. You have been provided with a series of "
            "research queries and their corresponding results in JSON format. "
            "Your task is to synthesize all of this information into a single, "
            "well-structured report. The report must follow this format exactly:\n\n"
            "1.  **TL;DR:** A brief, concise summary (2-4 sentences) of the most "
            "critical findings.\n"
            "2.  **Detailed Findings:** A comprehensive section that elaborates on the "
            "information discovered. Use markdown for formatting (e.g., headings, "
            "bullet points) to organize the content clearly. Synthesize information from "
            "different searches where appropriate."
        )

        messages = [
            {"role": "system", "content": report_prompt},
            {"role": "user", "content": json.dumps(self.research_data, indent=2)}
        ]

        final_report_message = self._call_ai(messages, use_tools=False)
        logging.info("Successfully generated final report.")
        return final_report_message.content


def main():
    """Main function to parse arguments and run the research agent."""
    parser = argparse.ArgumentParser(
        description="An autonomous agent to research topics using Google AI mode.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("topic", type=str, help="The research topic.")
    parser.add_argument(
        "-i", "--iterations", type=int, default=5,
        help="Maximum number of search iterations (default: 5)."
    )
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging.")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler("research_agent.log"),
            logging.StreamHandler()
        ]
    )

    try:
        agent = ResearchAgent(
            model=MODEL_NAME,
            api_base=OPENAI_API_BASE,
            api_key=OPENAI_API_KEY
        )
        final_report = agent.run(topic=args.topic, max_iterations=args.iterations)

        print("\n\n" + "="*80)
        print("                         FINAL RESEARCH REPORT")
        print("="*80 + "\n")
        print(final_report)
        print("\n" + "="*80)

    except Exception as e:
        logging.critical("A critical error occurred: %s", e, exc_info=True)
        print(f"\nA critical error occurred. Check research_agent.log for details.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()