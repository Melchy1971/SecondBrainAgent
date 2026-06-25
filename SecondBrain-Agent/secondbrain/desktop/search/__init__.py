"""Desktop search public exports."""

from .hybrid_search_ui import HybridCandidate, HybridScoreBreakdown, HybridSearchBackendAdapter, HybridSearchEngine, HybridSearchSettings
from .preview import SearchHighlight, SearchPreview, SearchPreviewBuilder, SearchPreviewSettings
from .saved_searches import SavedSearch, SavedSearchError, SavedSearchRepository, SavedSearchService
from .search_events import SearchEventBus
from .search_facets import FacetBucket, SearchFacets
from .search_filters import SearchFilters
from .search_history import SearchHistory
from .search_persistence import SearchPersistence
from .search_query import SearchQuery
from .search_result import SearchResult
from .search_service import InMemorySearchBackend, SearchBackend, SearchService
from .search_state import SearchState

__all__ = [
    "FacetBucket",
    "HybridCandidate",
    "HybridScoreBreakdown",
    "HybridSearchBackendAdapter",
    "HybridSearchEngine",
    "HybridSearchSettings",
    "InMemorySearchBackend",
    "SavedSearch",
    "SavedSearchError",
    "SavedSearchRepository",
    "SavedSearchService",
    "SearchBackend",
    "SearchEventBus",
    "SearchFacets",
    "SearchFilters",
    "SearchHighlight",
    "SearchHistory",
    "SearchPersistence",
    "SearchPreview",
    "SearchPreviewBuilder",
    "SearchPreviewSettings",
    "SearchQuery",
    "SearchResult",
    "SearchService",
    "SearchState",
]
