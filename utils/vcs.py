import os
import aiofiles
from database.memory import _execute_query, execute_update
from utils.logger import logger

class MAGMA_VCS:
    @staticmethod
    async def backup_file_before_edit(chat_id: int, project_name: str, file_path: str, full_disk_path: str):
        if not os.path.exists(full_disk_path): return
        try:
            async with aiofiles.open(full_disk_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            row = await _execute_query("SELECT MAX(version) FROM file_versions WHERE chat_id = ? AND file_path = ?", (chat_id, file_path), fetch_one=True)
            next_version = (row[0] or 0) + 1
            await execute_update(
                "INSERT INTO file_versions (chat_id, project_name, file_path, version, content, diff_summary) VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, project_name, file_path, next_version, content, f"Auto-backup (v{next_version})")
            )
        except Exception as e:
            logger.error(f"[VCS] Backup failed for {file_path}: {e}")

    @staticmethod
    async def rollback_file(chat_id: int, project_name: str, file_path: str, full_disk_path: str) -> bool:
        try:
            row = await _execute_query(
                "SELECT content, version FROM file_versions WHERE chat_id = ? AND file_path = ? ORDER BY version DESC LIMIT 1", 
                (chat_id, file_path), fetch_one=True
            )
            if not row: return False
            old_content, version = row
            async with aiofiles.open(full_disk_path, 'w', encoding='utf-8') as f:
                await f.write(old_content)
            await execute_update("DELETE FROM file_versions WHERE chat_id = ? AND file_path = ? AND version = ?", (chat_id, file_path, version))
            return True
        except Exception as e:
            return False