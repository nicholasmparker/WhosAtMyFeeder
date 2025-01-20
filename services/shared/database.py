from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the database connection pool"""
        db_path = os.path.join('/data', 'speciesid.db')
        
        # Create engine with connection pooling
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            connect_args={'check_same_thread': False}  # Required for SQLite
        )
        
        # Create session factory
        self.session_factory = scoped_session(
            sessionmaker(
                bind=self.engine,
                expire_on_commit=False
            )
        )
    
    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_write(self, operation, *args, **kwargs):
        """Execute a write operation within a transaction"""
        with self.session() as session:
            return operation(session, *args, **kwargs)
    
    def execute_read(self, operation, *args, **kwargs):
        """Execute a read operation"""
        with self.session() as session:
            return operation(session, *args, **kwargs)

# Global instance
db = DatabaseManager()
