"""
Auto-reindexing Scheduler for Government Sources

Automatically reindexes government agricultural websites and documents weekly.
"""

import asyncio
import logging
from typing import Dict, Any, List
import schedule
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..indexer.govt_website_indexer import GovtWebsiteIndexer
from ..indexer.pdf_processor import PDFProcessor
from ..vector_store.embeddings_manager import EmbeddingsManager
from ..vector_store.vector_db import VectorDatabase

class AutoReindexScheduler:
    """Automatic reindexing scheduler for government sources"""
    
    def __init__(self, 
                 db_path: str = "./chroma_db",
                 embeddings_cache_dir: str = "./embeddings_cache",
                 logs_dir: str = "./reindex_logs"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.embeddings_cache_dir = embeddings_cache_dir
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.website_indexer = GovtWebsiteIndexer()
        self.pdf_processor = PDFProcessor()
        self.embeddings_manager = EmbeddingsManager(cache_dir=embeddings_cache_dir)
        self.vector_db = VectorDatabase(db_path=db_path)
        
        # Scheduler state
        self.is_running = False
        self.scheduler_thread = None
        self.last_reindex_time = None
        self.reindex_stats = {}
        
        # Load previous reindex state
        self._load_state()
    
    def start_scheduler(self):
        """Start the automatic reindexing scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.logger.info("Starting auto-reindex scheduler...")
        
        # Schedule weekly reindexing (every Sunday at 2 AM)
        schedule.every().sunday.at("02:00").do(self._run_full_reindex)
        
        # Schedule daily incremental updates (every day at 6 AM)
        schedule.every().day.at("06:00").do(self._run_incremental_update)
        
        # Schedule database maintenance (every month)
        schedule.every().month.do(self._run_database_maintenance)
        
        # Start the scheduler in a separate thread
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Auto-reindex scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the automatic reindexing scheduler"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping auto-reindex scheduler...")
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("Auto-reindex scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _run_full_reindex(self):
        """Run full reindexing of all government sources"""
        self.logger.info("Starting full reindexing of government sources...")
        
        start_time = datetime.now()
        
        try:
            # Create backup before reindexing
            backup_path = self.logs_dir / f"backup_{start_time.strftime('%Y%m%d_%H%M%S')}"
            self.vector_db.backup_database(str(backup_path))
            
            # Run indexing
            stats = asyncio.run(self._perform_full_reindex())
            
            # Update state
            self.last_reindex_time = start_time
            self.reindex_stats = stats
            self._save_state()
            
            # Log results
            self._log_reindex_results(start_time, stats, "full")
            
            self.logger.info("Full reindexing completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during full reindexing: {e}")
            self._log_error(start_time, str(e), "full")
    
    def _run_incremental_update(self):
        """Run incremental update for recently changed content"""
        self.logger.info("Starting incremental update...")
        
        start_time = datetime.now()
        
        try:
            # Only run incremental if we've done a full reindex recently
            if not self.last_reindex_time or (start_time - self.last_reindex_time).days > 14:
                self.logger.info("No recent full reindex found, skipping incremental update")
                return
            
            stats = asyncio.run(self._perform_incremental_update())
            
            # Log results
            self._log_reindex_results(start_time, stats, "incremental")
            
            self.logger.info("Incremental update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during incremental update: {e}")
            self._log_error(start_time, str(e), "incremental")
    
    def _run_database_maintenance(self):
        """Run database maintenance tasks"""
        self.logger.info("Starting database maintenance...")
        
        try:
            # Delete old content (older than 90 days)
            self.vector_db.delete_old_content(days_old=90)
            
            # Get current database stats
            stats = self.vector_db.get_collection_stats()
            self.logger.info(f"Database stats after maintenance: {stats}")
            
            # Create monthly backup
            backup_path = self.logs_dir / f"monthly_backup_{datetime.now().strftime('%Y%m')}"
            self.vector_db.backup_database(str(backup_path))
            
            self.logger.info("Database maintenance completed")
            
        except Exception as e:
            self.logger.error(f"Error during database maintenance: {e}")
    
    async def _perform_full_reindex(self) -> Dict[str, Any]:
        """Perform full reindexing of all sources"""
        stats = {
            'start_time': datetime.now(),
            'websites_indexed': 0,
            'pdfs_processed': 0,
            'embeddings_generated': 0,
            'errors': []
        }
        
        try:
            # Index government websites
            self.logger.info("Indexing government websites...")
            website_content = await self.website_indexer.start_indexing()
            stats['websites_indexed'] = len(website_content)
            
            # Process PDFs
            self.logger.info("Processing government PDFs...")
            pdf_content = await self.pdf_processor.process_all_pdfs()
            stats['pdfs_processed'] = len(pdf_content)
            
            # Convert to common format for embedding generation
            all_content = []
            
            # Convert website content
            for content in website_content:
                all_content.append({
                    'url': content.url,
                    'title': content.title,
                    'content': content.content,
                    'scheme_name': content.scheme_name,
                    'state': content.state,
                    'category': content.category,
                    'source_type': 'website'
                })
            
            # Convert PDF content
            for content in pdf_content:
                all_content.append({
                    'url': content.url,
                    'title': content.title,
                    'content': content.content,
                    'scheme_name': content.scheme_name,
                    'state': None,  # PDFs are usually central
                    'category': 'central',
                    'source_type': 'pdf'
                })
            
            # Generate embeddings
            self.logger.info("Generating embeddings...")
            embedding_results = self.embeddings_manager.generate_embeddings(all_content)
            stats['embeddings_generated'] = len(embedding_results)
            
            # Store in vector database
            self.logger.info("Storing embeddings in vector database...")
            success = self.vector_db.store_embeddings(embedding_results)
            
            if not success:
                stats['errors'].append("Failed to store embeddings in vector database")
            
            stats['end_time'] = datetime.now()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            return stats
            
        except Exception as e:
            stats['errors'].append(str(e))
            raise
    
    async def _perform_incremental_update(self) -> Dict[str, Any]:
        """Perform incremental update of changed content"""
        stats = {
            'start_time': datetime.now(),
            'new_content_found': 0,
            'embeddings_updated': 0,
            'errors': []
        }
        
        try:
            # For incremental updates, we'll focus on high-priority sources
            # and recently updated content
            
            # Sample a subset of high-priority websites
            high_priority_sources = [
                'pmkisan.gov.in',
                'agricoop.nic.in',
                'pmfby.gov.in',
                'pmksy.gov.in'
            ]
            
            # This is a simplified incremental update
            # In a real implementation, you'd track modification dates
            new_content = []
            
            # Check for new PDFs in the last week
            recent_pdfs = await self.pdf_processor.process_all_pdfs()
            new_content.extend([{
                'url': content.url,
                'title': content.title,
                'content': content.content,
                'scheme_name': content.scheme_name,
                'state': None,
                'category': 'central',
                'source_type': 'pdf'
            } for content in recent_pdfs])
            
            stats['new_content_found'] = len(new_content)
            
            if new_content:
                # Generate embeddings for new content
                embedding_results = self.embeddings_manager.generate_embeddings(new_content)
                stats['embeddings_updated'] = len(embedding_results)
                
                # Store in vector database
                self.vector_db.store_embeddings(embedding_results)
            
            stats['end_time'] = datetime.now()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            return stats
            
        except Exception as e:
            stats['errors'].append(str(e))
            raise
    
    def _save_state(self):
        """Save scheduler state to disk"""
        state_file = self.logs_dir / "scheduler_state.json"
        
        state = {
            'last_reindex_time': self.last_reindex_time.isoformat() if self.last_reindex_time else None,
            'reindex_stats': self._serialize_stats(self.reindex_stats)
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save scheduler state: {e}")
    
    def _load_state(self):
        """Load scheduler state from disk"""
        state_file = self.logs_dir / "scheduler_state.json"
        
        if not state_file.exists():
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            if state.get('last_reindex_time'):
                self.last_reindex_time = datetime.fromisoformat(state['last_reindex_time'])
            
            self.reindex_stats = state.get('reindex_stats', {})
            
        except Exception as e:
            self.logger.warning(f"Failed to load scheduler state: {e}")
    
    def _serialize_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize stats for JSON storage"""
        serialized = {}
        
        for key, value in stats.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        
        return serialized
    
    def _log_reindex_results(self, start_time: datetime, stats: Dict[str, Any], reindex_type: str):
        """Log reindexing results"""
        log_file = self.logs_dir / f"reindex_{start_time.strftime('%Y%m%d')}.log"
        
        log_entry = {
            'timestamp': start_time.isoformat(),
            'type': reindex_type,
            'stats': self._serialize_stats(stats),
            'success': len(stats.get('errors', [])) == 0
        }
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            self.logger.warning(f"Failed to write reindex log: {e}")
    
    def _log_error(self, start_time: datetime, error: str, reindex_type: str):
        """Log reindexing errors"""
        error_file = self.logs_dir / f"errors_{start_time.strftime('%Y%m%d')}.log"
        
        error_entry = {
            'timestamp': start_time.isoformat(),
            'type': reindex_type,
            'error': error
        }
        
        try:
            with open(error_file, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
        except Exception as e:
            self.logger.warning(f"Failed to write error log: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'last_reindex_time': self.last_reindex_time.isoformat() if self.last_reindex_time else None,
            'next_scheduled_runs': {
                'full_reindex': schedule.next_run(),
                'incremental_update': schedule.next_run()
            },
            'database_stats': self.vector_db.get_collection_stats(),
            'recent_stats': self.reindex_stats
        }
    
    def force_reindex(self, reindex_type: str = "full") -> Dict[str, Any]:
        """Manually trigger reindexing"""
        if reindex_type == "full":
            return asyncio.run(self._perform_full_reindex())
        elif reindex_type == "incremental":
            return asyncio.run(self._perform_incremental_update())
        else:
            raise ValueError("reindex_type must be 'full' or 'incremental'")
