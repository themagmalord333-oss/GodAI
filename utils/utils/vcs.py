import os
import aiofiles
from database.memory import _execute_query, execute_update
from utils.logger import logger

class MAGMA_VCS:
    @staticmethod
    async def backup_file_before_edit(chat_id: int, project_name: str, file_path: str, full_disk_path: str):
        """Saves the current state of a file to the DB before the AI overwrites it."""
        if not os.path.exists(full_disk_path):
            return  # Brand new file, nothing to backup
        
        try:
            async with aiofiles.open(full_disk_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # Get the next version number
            row = await _execute_query(
                "SELECT MAX(version) FROM file_versions WHERE chat_id = ? AND file_path = ?", 
                (chat_id, file_path), fetch_one=True
            )
            next_version = (row[0] or 0) + 1

            # Save to Database Backup
            await execute_update(
                "INSERT INTO file_versions (chat_id, project_name, file_path, version, content, diff_summary) VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, project_name, file_path, next_version, content, f"Auto-backup prior to AI modification (v{next_version})")
            )
            logger.info(f"[VCS] Backed up {file_path} to DB (Version {next_version})")
            
        except Exception as e:
            logger.error(f"[VCS] Failed to backup {file_path}: {e}")

    @staticmethod
    async def rollback_file(chat_id: int, project_name: str, file_path: str, full_disk_path: str) -> bool:
        """Rolls back a file to its last known good version from the DB."""
        try:
            # Fetch the most recent version
            row = await _execute_query(
                "SELECT content, version FROM file_versions WHERE chat_id = ? AND file_path = ? ORDER BY version DESC LIMIT 1", 
                (chat_id, file_path), fetch_one=True
            )
            if not row:
                return False # No backups found
                
            old_content, version = row
            
            # Restore to disk
            async with aiofiles.open(full_disk_path, 'w', encoding='utf-8') as f:
                await f.write(old_content)
                
            # Delete that backup so we can roll back again if needed (pop from stack)
            await execute_update("DELETE FROM file_versions WHERE chat_id = ? AND file_path = ? AND version = ?", (chat_id, file_path, version))
            
            logger.info(f"[VCS] Rolled back {file_path} to Version {version}")
            return True
            
        except Exception as e:
            logger.error(f"[VCS] Rollback failed for {file_path}: {e}")
            return False