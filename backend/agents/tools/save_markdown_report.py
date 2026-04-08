"""Save Markdown Report Tool.

This module provides a tool for saving markdown content to local files.
"""

import os

from langchain_core.tools import tool


@tool()
def save_markdown_report(
    content: str, filename: str, directory: str = "research_outputs"
) -> str:
    """Save markdown content to a local file."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)

        if not filename.lower().endswith(".md"):
            filename += ".md"

        file_path = os.path.join(directory, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully saved report to: {os.path.abspath(file_path)}"
    except Exception as e:
        return f"Error saving markdown file: {str(e)}"
