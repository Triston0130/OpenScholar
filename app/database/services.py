# app/database/services.py
"""
Database service layer for OpenScholar
Provides high-level CRUD operations for all models
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import IntegrityError
import uuid

from .models import User, Collection, Paper, Tag, SearchHistory, APIUsage, UserSession
from .connection import get_session
from ..app_logging import get_logger

logger = get_logger("database_services")

class UserService:
    """Service for user-related database operations"""
    
    @staticmethod
    def create_user(session: Session, email: str, name: str, role: str, 
                   institution: str = None, **kwargs) -> User:
        """Create a new user"""
        try:
            user = User(
                email=email,
                name=name,
                role=role,
                institution=institution,
                **kwargs
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"User created: {email}", user_id=str(user.id))
            return user
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise ValueError(f"User with email {email} already exists")
    
    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return session.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_user(session: Session, user_id: str, **updates) -> Optional[User]:
        """Update user information"""
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        logger.info(f"User updated: {user.email}", user_id=str(user.id))
        return user
    
    @staticmethod
    def update_last_login(session: Session, user_id: str) -> None:
        """Update user's last login time"""
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login_at = datetime.utcnow()
            session.commit()

class CollectionService:
    """Service for collection-related database operations"""
    
    @staticmethod
    def create_collection(session: Session, user_id: str, name: str, 
                         description: str = None, **kwargs) -> Collection:
        """Create a new collection for a user"""
        collection = Collection(
            user_id=user_id,
            name=name,
            description=description,
            **kwargs
        )
        session.add(collection)
        session.commit()
        session.refresh(collection)
        
        logger.info(f"Collection created: {name}", user_id=user_id, collection_id=str(collection.id))
        return collection
    
    @staticmethod
    def get_user_collections(session: Session, user_id: str) -> List[Collection]:
        """Get all collections for a user"""
        return session.query(Collection).filter(
            Collection.user_id == user_id
        ).order_by(Collection.sort_order, Collection.created_at).all()
    
    @staticmethod
    def get_collection_by_id(session: Session, collection_id: str, user_id: str = None) -> Optional[Collection]:
        """Get collection by ID, optionally checking ownership"""
        query = session.query(Collection).filter(Collection.id == collection_id)
        if user_id:
            query = query.filter(Collection.user_id == user_id)
        return query.first()
    
    @staticmethod
    def update_collection(session: Session, collection_id: str, user_id: str, **updates) -> Optional[Collection]:
        """Update collection information"""
        collection = session.query(Collection).filter(
            and_(Collection.id == collection_id, Collection.user_id == user_id)
        ).first()
        
        if not collection:
            return None
        
        for key, value in updates.items():
            if hasattr(collection, key):
                setattr(collection, key, value)
        
        collection.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(collection)
        
        logger.info(f"Collection updated: {collection.name}", user_id=user_id, collection_id=str(collection.id))
        return collection
    
    @staticmethod
    def delete_collection(session: Session, collection_id: str, user_id: str) -> bool:
        """Delete a collection"""
        collection = session.query(Collection).filter(
            and_(Collection.id == collection_id, Collection.user_id == user_id)
        ).first()
        
        if not collection:
            return False
        
        session.delete(collection)
        session.commit()
        
        logger.info(f"Collection deleted: {collection.name}", user_id=user_id, collection_id=str(collection.id))
        return True
    
    @staticmethod
    def add_paper_to_collection(session: Session, collection_id: str, paper_id: str, 
                               user_id: str, notes: str = None, custom_tags: List[str] = None) -> bool:
        """Add a paper to a collection"""
        collection = session.query(Collection).filter(
            and_(Collection.id == collection_id, Collection.user_id == user_id)
        ).first()
        
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        
        if not collection or not paper:
            return False
        
        # Check if paper is already in collection
        if paper not in collection.papers:
            collection.papers.append(paper)
            collection.paper_count += 1
            collection.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Paper added to collection", 
                       user_id=user_id, 
                       collection_id=str(collection.id), 
                       paper_id=str(paper.id))
        
        return True
    
    @staticmethod
    def remove_paper_from_collection(session: Session, collection_id: str, paper_id: str, user_id: str) -> bool:
        """Remove a paper from a collection"""
        collection = session.query(Collection).filter(
            and_(Collection.id == collection_id, Collection.user_id == user_id)
        ).first()
        
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        
        if not collection or not paper:
            return False
        
        if paper in collection.papers:
            collection.papers.remove(paper)
            collection.paper_count = max(0, collection.paper_count - 1)
            collection.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Paper removed from collection", 
                       user_id=user_id, 
                       collection_id=str(collection.id), 
                       paper_id=str(paper.id))
        
        return True

class PaperService:
    """Service for paper-related database operations"""
    
    @staticmethod
    def create_or_update_paper(session: Session, paper_data: Dict[str, Any]) -> Paper:
        """Create a new paper or update existing one (by DOI)"""
        # Try to find existing paper by DOI
        existing_paper = None
        if paper_data.get('doi'):
            existing_paper = session.query(Paper).filter(Paper.doi == paper_data['doi']).first()
        
        if existing_paper:
            # Update existing paper
            for key, value in paper_data.items():
                if hasattr(existing_paper, key) and value is not None:
                    setattr(existing_paper, key, value)
            
            existing_paper.updated_at = datetime.utcnow()
            existing_paper.last_accessed = datetime.utcnow()
            session.commit()
            session.refresh(existing_paper)
            
            logger.info(f"Paper updated: {existing_paper.title[:50]}...", paper_id=str(existing_paper.id))
            return existing_paper
        else:
            # Create new paper
            paper = Paper(**paper_data)
            paper.last_accessed = datetime.utcnow()
            session.add(paper)
            session.commit()
            session.refresh(paper)
            
            logger.info(f"Paper created: {paper.title[:50]}...", paper_id=str(paper.id))
            return paper
    
    @staticmethod
    def get_paper_by_id(session: Session, paper_id: str) -> Optional[Paper]:
        """Get paper by ID"""
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            paper.last_accessed = datetime.utcnow()
            session.commit()
        return paper
    
    @staticmethod
    def get_paper_by_doi(session: Session, doi: str) -> Optional[Paper]:
        """Get paper by DOI"""
        return session.query(Paper).filter(Paper.doi == doi).first()
    
    @staticmethod
    def search_papers(session: Session, query: str, limit: int = 50, 
                     year_start: int = None, year_end: int = None,
                     sources: List[str] = None) -> List[Paper]:
        """Search papers in database"""
        db_query = session.query(Paper)
        
        # Text search in title and abstract
        if query:
            search_filter = or_(
                Paper.title.ilike(f'%{query}%'),
                Paper.abstract.ilike(f'%{query}%')
            )
            db_query = db_query.filter(search_filter)
        
        # Year range filter
        if year_start:
            db_query = db_query.filter(Paper.year >= str(year_start))
        if year_end:
            db_query = db_query.filter(Paper.year <= str(year_end))
        
        # Source filter
        if sources:
            db_query = db_query.filter(Paper.source.in_(sources))
        
        # Order by relevance (citation count desc, then creation date desc)
        db_query = db_query.order_by(
            desc(Paper.citation_count),
            desc(Paper.created_at)
        )
        
        return db_query.limit(limit).all()
    
    @staticmethod
    def get_collection_papers(session: Session, collection_id: str, user_id: str) -> List[Paper]:
        """Get all papers in a collection"""
        collection = session.query(Collection).filter(
            and_(Collection.id == collection_id, Collection.user_id == user_id)
        ).first()
        
        if not collection:
            return []
        
        return collection.papers

class TagService:
    """Service for tag-related database operations"""
    
    @staticmethod
    def create_tag(session: Session, name: str, user_id: str = None, 
                  category: str = None, **kwargs) -> Tag:
        """Create a new tag"""
        tag = Tag(
            name=name,
            user_id=user_id,
            category=category,
            **kwargs
        )
        session.add(tag)
        session.commit()
        session.refresh(tag)
        
        logger.info(f"Tag created: {name}", user_id=user_id, tag_id=str(tag.id))
        return tag
    
    @staticmethod
    def get_user_tags(session: Session, user_id: str) -> List[Tag]:
        """Get all tags for a user"""
        return session.query(Tag).filter(Tag.user_id == user_id).order_by(Tag.name).all()
    
    @staticmethod
    def get_system_tags(session: Session) -> List[Tag]:
        """Get all system tags"""
        return session.query(Tag).filter(Tag.is_system_tag == True).order_by(Tag.name).all()
    
    @staticmethod
    def add_tag_to_paper(session: Session, paper_id: str, tag_id: str) -> bool:
        """Add a tag to a paper"""
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        tag = session.query(Tag).filter(Tag.id == tag_id).first()
        
        if not paper or not tag:
            return False
        
        if tag not in paper.tags:
            paper.tags.append(tag)
            tag.usage_count += 1
            session.commit()
        
        return True

class SearchHistoryService:
    """Service for search history operations"""
    
    @staticmethod
    def log_search(session: Session, user_id: str, query: str, filters: Dict[str, Any],
                  results_count: int, sources_queried: List[str], 
                  search_duration_ms: int, cache_hit: bool = False,
                  session_id: str = None, user_agent: str = None, ip_address: str = None) -> SearchHistory:
        """Log a search query"""
        search_history = SearchHistory(
            user_id=user_id,
            query=query,
            filters=filters,
            results_count=results_count,
            sources_queried=sources_queried,
            search_duration_ms=search_duration_ms,
            cache_hit=cache_hit,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        session.add(search_history)
        session.commit()
        session.refresh(search_history)
        
        logger.info(f"Search logged: {query}", user_id=user_id, results_count=results_count)
        return search_history
    
    @staticmethod
    def get_user_search_history(session: Session, user_id: str, limit: int = 50) -> List[SearchHistory]:
        """Get user's search history"""
        return session.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.created_at)).limit(limit).all()
    
    @staticmethod
    def get_popular_searches(session: Session, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        popular = session.query(
            SearchHistory.query,
            func.count(SearchHistory.query).label('count')
        ).filter(
            SearchHistory.created_at >= since_date
        ).group_by(
            SearchHistory.query
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [{"query": query, "count": count} for query, count in popular]

class APIUsageService:
    """Service for API usage tracking"""
    
    @staticmethod
    def log_api_usage(session: Session, api_name: str, endpoint: str, 
                     response_status: int, response_time_ms: int,
                     results_returned: int = None, cache_hit: bool = False,
                     user_id: str = None, search_history_id: str = None,
                     **kwargs) -> APIUsage:
        """Log API usage"""
        api_usage = APIUsage(
            api_name=api_name,
            endpoint=endpoint,
            response_status=response_status,
            response_time_ms=response_time_ms,
            results_returned=results_returned,
            cache_hit=cache_hit,
            user_id=user_id,
            search_history_id=search_history_id,
            **kwargs
        )
        session.add(api_usage)
        session.commit()
        
        logger.info(f"API usage logged: {api_name}", 
                   status=response_status, 
                   duration_ms=response_time_ms)
        return api_usage
    
    @staticmethod
    def get_api_stats(session: Session, days: int = 7) -> Dict[str, Any]:
        """Get API usage statistics"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stats = session.query(
            APIUsage.api_name,
            func.count(APIUsage.id).label('total_calls'),
            func.avg(APIUsage.response_time_ms).label('avg_response_time'),
            func.sum(func.case([(APIUsage.response_status >= 200, 1), (APIUsage.response_status < 300, 1)], else_=0)).label('success_calls'),
            func.sum(func.case([(APIUsage.cache_hit == True, 1)], else_=0)).label('cache_hits')
        ).filter(
            APIUsage.created_at >= since_date
        ).group_by(
            APIUsage.api_name
        ).all()
        
        return {
            api_name: {
                "total_calls": total_calls,
                "avg_response_time_ms": float(avg_response_time) if avg_response_time else 0,
                "success_rate": (success_calls / total_calls) if total_calls > 0 else 0,
                "cache_hit_rate": (cache_hits / total_calls) if total_calls > 0 else 0
            }
            for api_name, total_calls, avg_response_time, success_calls, cache_hits in stats
        }

# Utility functions for database operations
def get_or_create_user(email: str, name: str, role: str, **kwargs) -> User:
    """Get existing user or create new one"""
    with get_session() as session:
        user = UserService.get_user_by_email(session, email)
        if not user:
            user = UserService.create_user(session, email, name, role, **kwargs)
        return user

def ensure_default_collection(user_id: str) -> Collection:
    """Ensure user has a default collection"""
    with get_session() as session:
        collections = CollectionService.get_user_collections(session, user_id)
        if not collections:
            return CollectionService.create_collection(
                session, user_id, "My Papers", "Default collection for saved papers"
            )
        return collections[0]
