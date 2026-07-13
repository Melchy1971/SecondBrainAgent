"""Wire M365 resource connectors and writers into the connector registry."""

from __future__ import annotations

from secondbrain.connectors.connector_registry import ConnectorRegistry
from secondbrain.connectors.microsoft.approval import ApprovalGate
from secondbrain.connectors.microsoft.graph_client import GraphClient
from secondbrain.connectors.microsoft.resources import (
    mail, calendar, contacts, onedrive, teams, todo, onenote,
)

# name -> (connector factory, writer class)
RESOURCES = {
    "mail": (mail.connector, mail.MailWriter),
    "calendar": (calendar.connector, calendar.CalendarWriter),
    "contacts": (contacts.connector, contacts.ContactsWriter),
    "onedrive": (onedrive.connector, onedrive.OneDriveWriter),
    "teams": (teams.connector, teams.TeamsWriter),
    "todo": (todo.connector, todo.TodoWriter),
    "onenote": (onenote.connector, onenote.OneNoteWriter),
}

RESOURCE_NAMES = tuple(RESOURCES.keys())


def build_connectors(client: GraphClient, resources=None) -> dict:
    selected = resources or RESOURCE_NAMES
    return {name: RESOURCES[name][0](client) for name in selected if name in RESOURCES}


def build_writers(client: GraphClient, gate: ApprovalGate, resources=None) -> dict:
    selected = resources or RESOURCE_NAMES
    return {name: RESOURCES[name][1](client, gate) for name in selected if name in RESOURCES}


def register_all(registry: ConnectorRegistry, client: GraphClient, resources=None) -> ConnectorRegistry:
    for name, conn in build_connectors(client, resources).items():
        registry.register(f"m365_{name}", conn)
    return registry
