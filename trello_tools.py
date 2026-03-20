# AUTO-GENERATED — do not edit manually.
# Re-generate with: python generate_trello_tools.py

import os
import httpx
from typing import Any, Optional

TRELLO_URL = os.environ.get("TRELLO_URL", "").rstrip("/")


def sync_cards_api_v1_cards_sync_post() -> Any:
    """Sync cards and lists from Trello"""
    url = f"{TRELLO_URL}/api/v1/cards/sync"
    query_params = {}
    json_data = None
    with httpx.Client() as client:
        response = client.post(url, params=query_params, json=json_data)
        response.raise_for_status()
        return response.json()


def get_current_lists_api_v1_current_lists_get() -> Any:
    """Get all current lists"""
    url = f"{TRELLO_URL}/api/v1/current-lists"
    query_params = {}
    with httpx.Client() as client:
        response = client.get(url, params=query_params)
        response.raise_for_status()
        return response.json()


def add_current_list_api_v1_current_lists_post(list_id: str) -> Any:
    """Add a current list"""
    url = f"{TRELLO_URL}/api/v1/current-lists"
    query_params = {}
    json_data = {k: v for k, v in {
        "list_id": list_id,
    }.items() if v is not None}
    with httpx.Client() as client:
        response = client.post(url, params=query_params, json=json_data)
        response.raise_for_status()
        return response.json()


def remove_current_list_api_v1_current_lists__list_id__delete(list_id: str) -> Any:
    """Remove a current list"""
    url = f"{TRELLO_URL}/api/v1/current-lists/{list_id}"
    query_params = {}
    json_data = None
    with httpx.Client() as client:
        response = client.delete(url, params=query_params, json=json_data)
        response.raise_for_status()
        return response.json()


def get_current_cards_api_v1_current_lists_cards_get() -> Any:
    """Get cards from current lists"""
    url = f"{TRELLO_URL}/api/v1/current-lists/cards"
    query_params = {}
    with httpx.Client() as client:
        response = client.get(url, params=query_params)
        response.raise_for_status()
        return response.json()


def notify_discord_api_v1_current_lists_notify_discord_post() -> Any:
    """Send current cards to Discord"""
    url = f"{TRELLO_URL}/api/v1/current-lists/notify-discord"
    query_params = {}
    json_data = None
    with httpx.Client() as client:
        response = client.post(url, params=query_params, json=json_data)
        response.raise_for_status()
        return response.json()


def health_health_get() -> Any:
    """Health"""
    url = f"{TRELLO_URL}/health"
    query_params = {}
    with httpx.Client() as client:
        response = client.get(url, params=query_params)
        response.raise_for_status()
        return response.json()


def register_trello_tools(mcp) -> None:
    """Register all generated Trello API tools with the MCP server."""
    mcp.tool(description="Add a current list")(add_current_list_api_v1_current_lists_post)
    mcp.tool(description="Remove a current list")(remove_current_list_api_v1_current_lists__list_id__delete)
    mcp.tool(description="Get all processing card Today")(get_current_cards_api_v1_current_lists_cards_get)
