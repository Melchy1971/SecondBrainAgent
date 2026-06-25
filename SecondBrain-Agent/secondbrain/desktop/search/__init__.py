"""Public desktop search API."""

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

__all__ = [name for name in globals() if not name.startswith("_")]
