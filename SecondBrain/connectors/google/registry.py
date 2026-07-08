"""Wire Google resource connectors and writers into the connector registry."""

from __future__ import annotations

from secondbrain.connectors.connector_registry import ConnectorRegistry
from secondbrain.connectors.google.resources import gmail, calendar, drive, contacts, tasks

RESOURCES = {
    "gmail": (gmail.connector, gmail.GmailWriter),
    "calendar": (calendar.connector, calendar.CalendarWriter),
    "drive": (drive.connector, drive.DriveWriter),
    "contacts": (contacts.connector, contacts.ContactsWriter),
    "tasks": (tasks.connector, tasks.TasksWriter),
}
RESOURCE_NAMES = tuple(RESOURCES.keys())


def build_connectors(client, resources=None) -> dict:
    selected = resources or RESOURCE_NAMES
    return {name: RESOURCES[name][0](client) for name in selected if name in RESOURCES}


def build_writers(client, gate, resources=None) -> dict:
    selected = resources or RESOURCE_NAMES
    return {name: RESOURCES[name][1](client, gate) for name in selected if name in RESOURCES}


def register_all(registry: ConnectorRegistry, client, resources=None) -> ConnectorRegistry:
    for name, conn in build_connectors(client, resources).items():
        registry.register(f"google_{name}", conn)
    return registry
