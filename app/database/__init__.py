# Database module for OpenScholar
from .connection import (
    DatabaseManager,
    initialize_database,
    create_tables,
    get_session,
    get_db_session,
    get_db,
    check_database_health,
    db_manager
)
from .models import (
    Base,
    User,
    Collection,
    Paper,
    Tag,
    SearchHistory,
    APIUsage,
    UserSession
)
# Import user settings models to register them with SQLAlchemy
from .user_settings import UserEmailSettings, UserNotificationPreferences
# Import sharing models to register them with SQLAlchemy  
from .sharing_models import CollectionShare, FolderShare, Folder, PDFAnnotation, AnnotationReply, PDFCache
from .services import (
    UserService,
    CollectionService,
    PaperService,
    TagService,
    SearchHistoryService,
    APIUsageService,
    get_or_create_user,
    ensure_default_collection
)

__all__ = [
    # Connection management
    'DatabaseManager',
    'initialize_database',
    'create_tables',
    'get_session',
    'get_db_session',
    'get_db',
    'check_database_health',
    'db_manager',
    
    # Models
    'Base',
    'User',
    'Collection', 
    'Paper',
    'Tag',
    'SearchHistory',
    'APIUsage',
    'UserSession',
    
    # Services
    'UserService',
    'CollectionService',
    'PaperService',
    'TagService',
    'SearchHistoryService',
    'APIUsageService',
    'get_or_create_user',
    'ensure_default_collection'
]
