"""Public desktop dashboard API."""

from .actions import DashboardAction, DashboardActionExecutor, DashboardActionRegistry, DashboardActionResult, DashboardActionService, DashboardActionStatus, DashboardActionType
from .dashboard_events import DashboardEvent, DashboardEventLog, DashboardEventType
from .dashboard_persistence import DashboardPersistence
from .dashboard_service import DashboardService
from .dashboard_state import DashboardState
from .layout import DashboardLayout, DashboardLayoutPersistence, DashboardLayoutService, DashboardLayoutValidator, LayoutValidationResult, LayoutValidationStatus, WidgetPosition
from .rc_gate import DashboardRCFinding, DashboardRCGate, DashboardRCReport, DashboardRCSnapshot, DashboardRCSeverity, DashboardRCStatus, evaluate_dashboard_rc
from .rc_report import dashboard_rc_markdown, write_dashboard_rc_markdown, write_dashboard_rc_report
from .refresh_scheduler import RefreshScheduler
from .widget_base import DashboardWidget, WidgetStatus
from .widget_manager import WidgetManager
from .widget_providers import ConnectorHealthProvider, HealthColor, RagStatusProvider, RecentErrorsProvider, RecentImportsProvider, RunningJobsProvider, StorageUsageProvider, SystemHealthProvider, WidgetDataSource, WorkspaceSummaryProvider, default_widget_providers
from .widget_registry import WidgetRegistry, WidgetRegistryError

__all__ = [name for name in globals() if not name.startswith("_")]
