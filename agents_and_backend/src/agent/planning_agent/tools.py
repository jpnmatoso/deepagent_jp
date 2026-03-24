"""Planning Tools.

This module provides tools for the planning agent.
"""

import os

import httpx
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

tavily_client = TavilyClient()

BDC_BASE_URL = os.getenv("BDC_BASE_URL", "http://localhost:8100")


def _get_bdc_headers() -> dict:
    """Faz login via passkey e retorna headers com Bearer token."""
    passkey = os.getenv("BDC_PASSKEY")
    if not passkey:
        raise ValueError("BDC_PASSKEY não configurado")

    response = httpx.post(
        f"{BDC_BASE_URL}/auth/login", json={"passkey": passkey}, timeout=30.0
    )
    response.raise_for_status()
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


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


def _normalize_task_status(status: str) -> str:
    """Normalize task status to API format."""
    normalized = status.lower().strip()
    status_map = {
        "espera": "waiting",
        "waiting": "waiting",
        "aberta": "open",
        "open": "open",
        "sprint": "sprint",
        "concluida": "done",
        "concluído": "done",
        "done": "done",
        "feita": "done",
        "falha": "failure",
        "failure": "failure",
        "falhou": "failure",
        "insucesso": "failure",
        "failed": "failure",
    }
    return status_map.get(normalized, status)


@tool()
def projects_manager(
    action: Annotated[
        Literal["list", "create", "get", "update", "delete", "search"],
        "CRUD action: list, create, get, update, delete, or search",
    ],
    title: Annotated[
        str | None,
        "Project title (required for create, optional for update)",
    ] = None,
    body: Annotated[
        str | None,
        "Project description/body text",
    ] = None,
    status: Annotated[
        str | None,
        "Project status (e.g., 'active')",
    ] = None,
    project_id: Annotated[
        int | None,
        "Project ID (required for get, update, delete)",
    ] = None,
    query: Annotated[
        str | None,
        "Search query (for search action)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results to return",
    ] = 50,
) -> str:
    """Manage projects in JP BDC API with full CRUD operations."""
    headers = _get_bdc_headers()

    if action == "list":
        response = httpx.get(
            f"{BDC_BASE_URL}/projects",
            params={"limit": limit},
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        projects = response.json()
        if not projects:
            return "No projects found."
        result_lines = []
        for p in projects:
            result_lines.append(
                f"- [{p['id']}] {p['title']} | status: {p['status']} | "
                f"docs: {p.get('document_count', 0)} | tasks: {p.get('task_count', 0)}"
            )
        return f"Projects ({len(projects)}):\n" + "\n".join(result_lines)

    elif action == "create":
        if not title:
            return "Error: 'title' is required to create a project."
        payload = {"title": title}
        if body is not None:
            payload["body"] = body
        if status is not None:
            normalized_status = status.lower().strip()
            if normalized_status in ["inativo", "inactive", "archived"]:
                payload["status"] = "inactive"
            elif normalized_status in ["ativo", "active"]:
                payload["status"] = "active"
            else:
                payload["status"] = status
        response = httpx.post(
            f"{BDC_BASE_URL}/projects", json=payload, headers=headers, timeout=30.0
        )
        response.raise_for_status()
        project = response.json()
        return (
            f"Project created successfully!\n"
            f"ID: {project['id']}\n"
            f"Title: {project['title']}\n"
            f"Status: {project['status']}"
        )

    elif action == "get":
        if not project_id:
            return "Error: 'project_id' is required to get a project."
        response = httpx.get(
            f"{BDC_BASE_URL}/projects/{project_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Project with ID {project_id} not found."
        response.raise_for_status()
        p = response.json()
        return (
            f"Project [{p['id']}]: {p['title']}\n"
            f"Status: {p['status']}\n"
            f"Body: {p.get('body') or 'N/A'}\n"
            f"Documents: {p.get('document_count', 0)} | Tasks: {p.get('task_count', 0)}\n"
            f"Created: {p.get('created_at', 'N/A')}"
        )

    elif action == "update":
        if not project_id:
            return "Error: 'project_id' is required to update a project."
        payload = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if status is not None:
            normalized_status = status.lower().strip()
            if normalized_status in ["inativo", "inactive", "archived"]:
                payload["status"] = "inactive"
            elif normalized_status in ["ativo", "active"]:
                payload["status"] = "active"
            else:
                payload["status"] = status
        if not payload:
            return (
                "Error: Provide at least one field to update (title, body, or status)."
            )
        response = httpx.put(
            f"{BDC_BASE_URL}/projects/{project_id}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 404:
            return f"Project with ID {project_id} not found."
        if response.status_code == 422:
            return f"Error 422: Invalid data sent to API.\nPayload: {payload}\nResponse: {response.text}"
        response.raise_for_status()
        p = response.json()
        return f"Project [{p['id']}] updated successfully!\nTitle: {p['title']}\nStatus: {p['status']}"

    elif action == "delete":
        if not project_id:
            return "Error: 'project_id' is required to delete a project."
        response = httpx.delete(
            f"{BDC_BASE_URL}/projects/{project_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Project with ID {project_id} not found."
        response.raise_for_status()
        return f"Project {project_id} deleted successfully."

    elif action == "search":
        payload: dict = {"limit": limit}
        if query is not None:
            payload["query"] = query
        response = httpx.post(
            f"{BDC_BASE_URL}/projects/search",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        projects = response.json()
        if not projects:
            return f"No projects found matching query: {query or '(empty)'}"
        result_lines = []
        for p in projects:
            result_lines.append(f"- [{p['id']}] {p['title']} | status: {p['status']}")
        return f"Search results ({len(projects)}):\n" + "\n".join(result_lines)

    return f"Unknown action: {action}"


@tool()
def tasks_manager(
    action: Annotated[
        Literal["list", "create", "get", "update", "delete", "search", "sprint"],
        "CRUD action: list, create, get, update, delete, search, or sprint",
    ],
    title: Annotated[
        str | None,
        "Task title (required for create, optional for update)",
    ] = None,
    body: Annotated[
        str | None,
        "Task description/body text",
    ] = None,
    status: Annotated[
        str | None,
        "Task status: waiting, open, sprint, or done",
    ] = None,
    category: Annotated[
        str | None,
        "Task category (e.g., 'circumstantial')",
    ] = None,
    project_id: Annotated[
        int | None,
        "Associated project ID",
    ] = None,
    task_id: Annotated[
        int | None,
        "Task ID (required for get, update, delete)",
    ] = None,
    query: Annotated[
        str | None,
        "Search query (for search action)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results to return",
    ] = 50,
) -> str:
    """Manage tasks in JP BDC API with full CRUD operations."""
    headers = _get_bdc_headers()

    if action == "list":
        params: dict = {"limit": limit}
        if project_id is not None:
            params["project_id"] = project_id
        if category is not None:
            params["category"] = category
        if status is not None:
            normalized = _normalize_task_status(status)
            if normalized in ["sprint", "waiting"]:
                params["status"] = normalized
        else:
            params["status"] = "sprint,waiting"
        response = httpx.get(
            f"{BDC_BASE_URL}/tasks",
            params=params,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        tasks = response.json()
        if not tasks:
            return "No tasks found."
        result_lines = []
        for t in tasks:
            result_lines.append(
                f"- [{t['id']}] {t['title']} | {t['status']} | {t.get('category', 'N/A')}"
            )
        return f"Tasks ({len(tasks)}):\n" + "\n".join(result_lines)

    elif action == "sprint":
        response = httpx.get(
            f"{BDC_BASE_URL}/tasks/sprint",
            params={"limit": limit},
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        tasks = response.json()
        if not tasks:
            return "No sprint tasks found."
        result_lines = [f"- [{t['id']}] {t['title']}" for t in tasks]
        return f"Sprint Tasks ({len(tasks)}):\n" + "\n".join(result_lines)

    elif action == "create":
        if not title:
            return "Error: 'title' is required to create a task."
        payload: dict = {"title": title}
        if body is not None:
            payload["body"] = body
        if status is not None:
            payload["status"] = _normalize_task_status(status)
        if category is not None:
            payload["category"] = category
        if project_id is not None:
            payload["project_id"] = project_id
        response = httpx.post(
            f"{BDC_BASE_URL}/tasks", json=payload, headers=headers, timeout=30.0
        )
        response.raise_for_status()
        task = response.json()
        return (
            f"Task created successfully!\n"
            f"ID: {task['id']}\n"
            f"Title: {task['title']}\n"
            f"Status: {task['status']}\n"
            f"Category: {task.get('category', 'N/A')}"
        )

    elif action == "get":
        if not task_id:
            return "Error: 'task_id' is required to get a task."
        response = httpx.get(
            f"{BDC_BASE_URL}/tasks/{task_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Task with ID {task_id} not found."
        response.raise_for_status()
        t = response.json()
        return (
            f"Task [{t['id']}]: {t['title']}\n"
            f"Status: {t['status']}\n"
            f"Category: {t.get('category', 'N/A')}\n"
            f"Project ID: {t.get('project_id', 'N/A')}\n"
            f"Body: {t.get('body') or 'N/A'}\n"
            f"Created: {t.get('created_at', 'N/A')}"
        )

    elif action == "update":
        if not task_id:
            return "Error: 'task_id' is required to update a task."
        existing_task = httpx.get(
            f"{BDC_BASE_URL}/tasks/{task_id}", headers=headers, timeout=30.0
        )
        if existing_task.status_code == 404:
            return f"Task with ID {task_id} not found."
        existing_task.raise_for_status()
        current_task = existing_task.json()
        payload: dict = {
            "title": title if title is not None else current_task.get("title", ""),
            "body": body if body is not None else current_task.get("body", ""),
            "category": category
            if category is not None
            else current_task.get("category", "circumstantial"),
            "status": _normalize_task_status(status)
            if status is not None
            else current_task.get("status", "waiting"),
            "project_id": project_id
            if project_id is not None
            else current_task.get("project_id"),
        }
        response = httpx.put(
            f"{BDC_BASE_URL}/tasks/{task_id}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 404:
            return f"Task with ID {task_id} not found."
        if response.status_code == 422:
            return f"Error 422: Invalid data sent to API.\nPayload: {payload}\nResponse: {response.text}"
        response.raise_for_status()
        t = response.json()
        return f"Task [{t['id']}] updated successfully!\nTitle: {t['title']}\nStatus: {t['status']}"

    elif action == "delete":
        if not task_id:
            return "Error: 'task_id' is required to delete a task."
        response = httpx.delete(
            f"{BDC_BASE_URL}/tasks/{task_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Task with ID {task_id} not found."
        response.raise_for_status()
        return f"Task {task_id} deleted successfully."

    elif action == "search":
        payload: dict = {"limit": limit}
        if query is not None:
            payload["query"] = query
        if project_id is not None:
            payload["project_id"] = project_id
        if status is not None:
            payload["status"] = _normalize_task_status(status)
        if category is not None:
            payload["category"] = category
        response = httpx.post(
            f"{BDC_BASE_URL}/tasks/search",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        tasks = response.json()
        if not tasks:
            return f"No tasks found matching query: {query or '(empty)'}"
        result_lines = [
            f"- [{t['id']}] {t['title']} | status: {t['status']}" for t in tasks
        ]
        return f"Search results ({len(tasks)}):\n" + "\n".join(result_lines)

    return f"Unknown action: {action}"


def _normalize_document_status(status: str) -> str:
    """Normalize document status to API format."""
    normalized = status.lower().strip()
    status_map = {
        "publicado": "published",
        "published": "published",
        "rascunho": "draft",
        "draft": "draft",
        "arquivado": "archived",
        "archived": "archived",
    }
    return status_map.get(normalized, status)


def _normalize_tags(tags_input: str | list[str] | None) -> list[str] | None:
    """Normalize tags to a list of strings."""
    import json

    if tags_input is None:
        return None
    if isinstance(tags_input, list):
        return [t.strip() for t in tags_input if t.strip()]
    if isinstance(tags_input, str):
        tags_input = tags_input.strip()
        if not tags_input:
            return None
        if tags_input.startswith("["):
            try:
                parsed = json.loads(tags_input)
                if isinstance(parsed, list):
                    return [t.strip() for t in parsed if t.strip()]
            except (json.JSONDecodeError, ValueError):
                pass
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        return tags if tags else None
    return None


@tool()
def documents_manager(
    action: Annotated[
        Literal["list", "create", "get", "update", "delete", "search"],
        "CRUD action: list, create, get, update, delete, or search",
    ],
    title: Annotated[
        str | None,
        "Document title (required for create, optional for update)",
    ] = None,
    body: Annotated[
        str | None,
        "Document content/body text",
    ] = None,
    tags: Annotated[
        str | list[str] | None,
        "List of tags or comma-separated string",
    ] = None,
    project_id: Annotated[
        int | None,
        "Associated project ID",
    ] = None,
    author: Annotated[
        str | None,
        "Document author name",
    ] = None,
    status: Annotated[
        str | None,
        "Document status: published, draft, or archived",
    ] = None,
    doc_id: Annotated[
        int | None,
        "Document ID (required for get, update, delete)",
    ] = None,
    references: Annotated[
        list[int] | None,
        "List of referenced document IDs",
    ] = None,
    query: Annotated[
        str | None,
        "Search query (for search action)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results to return",
    ] = 10,
) -> str:
    """Manage documents in JP BDC API with full CRUD operations."""
    headers = _get_bdc_headers()

    if action == "list":
        params: dict = {"limit": limit, "status": "published"}
        if project_id is not None:
            params["project_id"] = project_id
        response = httpx.get(
            f"{BDC_BASE_URL}/documents",
            params=params,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        docs = response.json()
        if not docs:
            return "No documents found."
        result_lines = []
        for d in docs:
            tags_str = ", ".join(d.get("tags", [])) if d.get("tags") else "no tags"
            result_lines.append(
                f"- [{d['id']}] {d['title']} | author: {d.get('author', 'N/A')} | tags: {tags_str}"
            )
        return f"Documents ({len(docs)}):\n" + "\n".join(result_lines)

    elif action == "create":
        if not title:
            return "Error: 'title' is required to create a document."
        if not body:
            return "Error: 'body' is required to create a document."
        payload: dict = {"title": title, "body": body}
        normalized_tags = _normalize_tags(tags)
        if normalized_tags is not None:
            payload["tags"] = normalized_tags
        if project_id is not None:
            payload["project_id"] = project_id
        if author is not None:
            payload["author"] = author
        else:
            payload["author"] = "agent"
        if status is not None:
            payload["status"] = _normalize_document_status(status)
        else:
            payload["status"] = "published"
        if references is not None:
            payload["references"] = references
        response = httpx.post(
            f"{BDC_BASE_URL}/documents", json=payload, headers=headers, timeout=30.0
        )
        response.raise_for_status()
        doc = response.json()
        return (
            f"Document created successfully!\n"
            f"ID: {doc['id']}\n"
            f"Title: {doc['title']}\n"
            f"Status: {doc['status']}\n"
            f"Author: {doc.get('author', 'N/A')}"
        )

    elif action == "get":
        if not doc_id:
            return "Error: 'doc_id' is required to get a document."
        response = httpx.get(
            f"{BDC_BASE_URL}/documents/{doc_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Document with ID {doc_id} not found."
        response.raise_for_status()
        d = response.json()
        tags_str = ", ".join(d.get("tags", [])) if d.get("tags") else "no tags"
        refs = d.get("references") if d.get("references") else []
        return (
            f"Document [{d['id']}]: {d['title']}\n"
            f"Author: {d.get('author', 'N/A')}\n"
            f"Status: {d['status']}\n"
            f"Project ID: {d.get('project_id', 'N/A')}\n"
            f"Tags: {tags_str}\n"
            f"References: {refs or 'none'}\n"
            f"Created: {d.get('created_at', 'N/A')}\n"
            f"---\n"
            f"Content:\n{d.get('body', 'N/A')}"
        )

    elif action == "update":
        if not doc_id:
            return "Error: 'doc_id' is required to update a document."
        existing_response = httpx.get(
            f"{BDC_BASE_URL}/documents/{doc_id}", headers=headers, timeout=30.0
        )
        if existing_response.status_code == 404:
            return f"Document with ID {doc_id} not found."
        existing_response.raise_for_status()
        existing_doc = existing_response.json()
        payload: dict = {
            "title": title if title is not None else existing_doc.get("title", ""),
            "body": body if body is not None else existing_doc.get("body", ""),
            "tags": _normalize_tags(tags)
            if tags is not None
            else existing_doc.get("tags", []),
            "author": author
            if author is not None
            else existing_doc.get("author", "agent"),
        }
        if project_id is not None:
            payload["project_id"] = project_id
        if status is not None:
            payload["status"] = _normalize_document_status(status)
        else:
            payload["status"] = existing_doc.get("status", "published")
        if references is not None:
            payload["references"] = references
        response = httpx.put(
            f"{BDC_BASE_URL}/documents/{doc_id}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 404:
            return f"Document with ID {doc_id} not found."
        if response.status_code == 422:
            return f"Error 422: Invalid data sent to API.\nPayload: {payload}\nResponse: {response.text}"
        response.raise_for_status()
        d = response.json()
        return f"Document [{d['id']}] updated successfully!\nTitle: {d['title']}\nStatus: {d['status']}"

    elif action == "delete":
        if not doc_id:
            return "Error: 'doc_id' is required to delete a document."
        response = httpx.delete(
            f"{BDC_BASE_URL}/documents/{doc_id}", headers=headers, timeout=30.0
        )
        if response.status_code == 404:
            return f"Document with ID {doc_id} not found."
        response.raise_for_status()
        return f"Document {doc_id} deleted successfully."

    elif action == "search":
        payload: dict = {"limit": limit}
        if query is not None:
            payload["query"] = query
        if project_id is not None:
            payload["project_id"] = project_id
        if status is not None:
            payload["status"] = _normalize_document_status(status)
        response = httpx.post(
            f"{BDC_BASE_URL}/documents/search",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        docs = response.json()
        if not docs:
            return f"No documents found matching query: {query or '(empty)'}"
        result_lines = []
        for d in docs:
            tags_str = ", ".join(d.get("tags", [])) if d.get("tags") else "no tags"
            result_lines.append(
                f"- [{d['id']}] {d['title']} | status: {d['status']} | tags: {tags_str}"
            )
        return f"Search results ({len(docs)}):\n" + "\n".join(result_lines)

    return f"Unknown action: {action}"
