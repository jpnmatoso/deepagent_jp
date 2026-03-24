"""Research Tools.

This module provides search and content processing utilities for the research agent,
using Tavily for URL discovery and fetching full webpage content.
"""

import os

import httpx
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

tavily_client = TavilyClient()


def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return markdownify(response.text)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"


@tool()
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """Search the web for information on a given query."""
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]
        content = fetch_webpage_content(url)
        result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
        result_texts.append(result_text)

    response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""

    return response


@tool()
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making."""
    return f"Reflection recorded: {reflection}"


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
