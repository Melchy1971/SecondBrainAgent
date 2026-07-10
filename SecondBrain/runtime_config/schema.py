"""Konfigurationsschema: alle Keys, Defaults und Pflichtregeln an einer Stelle.

Jeder Default ist hier dokumentiert; es gibt keine hart codierten lokalen Pfade.
Pfad-Defaults sind relativ zum Workspace und werden zur Laufzeit aufgelöst.
"""

from __future__ import annotations

from dataclasses import dataclass

SECTION_AI = "KI / Embedding"
SECTION_DB = "Datenbank / Speicher"
SECTION_GUI = "GUI / Allgemein"
SECTION_VOICE = "Sprache / Voice"
SECTION_PATHS = "Pfade / Workspace"
SECTION_SECRETS = "Sicherheit / Secrets"

SECTIONS: tuple[str, ...] = (
    SECTION_AI, SECTION_DB, SECTION_GUI, SECTION_VOICE, SECTION_PATHS, SECTION_SECRETS,
)


@dataclass(frozen=True)
class ConfigKey:
    key: str
    section: str
    type: str = "string"  # string | int | float | bool | choice | secret | relpath
    default: str = ""
    choices: tuple[str, ...] = ()
    description: str = ""
    # "KEY==value" -> dieser Key ist Pflicht, wenn die Bedingung erfüllt ist.
    # "" -> optional; "*" -> immer Pflicht.
    required_if: str = ""

    @property
    def secret(self) -> bool:
        return self.type == "secret"


CONFIG_KEYS: tuple[ConfigKey, ...] = (
    # --- KI / Embedding ---
    ConfigKey("SECONDBRAIN_EMBEDDING_PROVIDER", SECTION_AI, "choice", "local",
              ("local", "ollama", "openai"),
              "Quelle für Embeddings. 'openai' erfordert API-Key, 'ollama' einen laufenden Dienst.", "*"),
    ConfigKey("SECONDBRAIN_EMBEDDING_MODEL", SECTION_AI, "string", "",
              (), "Modellname (leer = Provider-Standard)."),
    ConfigKey("SECONDBRAIN_EMBEDDING_DIMENSIONS", SECTION_AI, "int", "",
              (), "Vektordimensionen (leer = Modell-Standard)."),
    ConfigKey("SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS", SECTION_AI, "float", "10",
              (), "Maximale Wartezeit pro Embedding-Aufruf in Sekunden."),
    ConfigKey("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", SECTION_AI, "bool", "false",
              (), "Bei Provider-Ausfall auf lokalen Provider zurückfallen."),
    ConfigKey("SECONDBRAIN_OLLAMA_BASE_URL", SECTION_AI, "string", "http://localhost:11434",
              (), "Basis-URL des Ollama-Dienstes; nur relevant bei Provider 'ollama'.",
              "SECONDBRAIN_EMBEDDING_PROVIDER==ollama"),
    # --- Datenbank / Speicher ---
    ConfigKey("SECONDBRAIN_VECTOR_STORE", SECTION_DB, "choice", "sqlite",
              ("sqlite", "pgvector"),
              "Vektor-Store. 'pgvector' erfordert DATABASE_URL."),
    ConfigKey("DATABASE_URL", SECTION_DB, "secret", "",
              (), "PostgreSQL-Verbindung (postgresql://USER:PASSWORT@HOST:PORT/DB). Enthält das DB-Passwort.",
              "SECONDBRAIN_VECTOR_STORE==pgvector"),
    # --- GUI / Allgemein ---
    ConfigKey("SECONDBRAIN_GUI_THEME", SECTION_GUI, "choice", "dark", ("dark", "light"),
              "Farbschema der Desktop-GUI."),
    ConfigKey("SECONDBRAIN_GUI_HOST", SECTION_GUI, "string", "127.0.0.1",
              (), "Bind-Adresse des sekundären Web-HUD."),
    ConfigKey("SECONDBRAIN_GUI_PORT", SECTION_GUI, "int", "8765",
              (), "Port des sekundären Web-HUD."),
    ConfigKey("SECONDBRAIN_PROFILE", SECTION_GUI, "string", "default",
              (), "Aktives Laufzeitprofil (z.B. default, dev)."),
    ConfigKey("SECONDBRAIN_UI_MODE", SECTION_GUI, "choice", "native", ("native", "web"),
              "Primäre Oberfläche des Launchers."),
    # --- Sprache / Voice ---
    ConfigKey("SECONDBRAIN_VOICE_LANGUAGE", SECTION_VOICE, "choice", "de-DE",
              ("de-DE", "en-US"), "Sprache des Offline-Intent-Parsers."),
    # --- Pfade / Workspace (relativ zum Workspace; keine absoluten Defaults) ---
    ConfigKey("SECONDBRAIN_VAULT_DIR", SECTION_PATHS, "relpath", "SecondBrain",
              (), "Obsidian-Vault, relativ zum Workspace (absolut erlaubt, aber kein Default)."),
    ConfigKey("SECONDBRAIN_INBOX_DIR", SECTION_PATHS, "relpath", "SecondBrain-Inbox",
              (), "Eingangsordner für Importe, relativ zum Workspace."),
    # --- Sicherheit / Secrets ---
    ConfigKey("OPENAI_API_KEY", SECTION_SECRETS, "secret", "",
              (), "OpenAI API-Key; Pflicht bei Embedding-Provider 'openai'.",
              "SECONDBRAIN_EMBEDDING_PROVIDER==openai"),
)

KEYS_BY_NAME: dict[str, ConfigKey] = {key.key: key for key in CONFIG_KEYS}
