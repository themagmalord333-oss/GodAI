import os
import re
import aiofiles
from config import Config
from utils.vcs import MAGMA_VCS
from utils.logger import logger

class FileManager:
    @staticmethod
    async def read_project_context(project_name: str) -> str:
        """Scans the project directory and returns all code files as a string for the AI's context."""
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        if not os.path.exists(project_dir):
            return "No existing files in this project. Starting from scratch."

        context_parts = ["CURRENT PROJECT STATE:\n"]
        ignore_dirs = {'.git', '__pycache__', 'venv', 'env', 'node_modules', '.magma'}
        ignore_exts = {'.png', '.jpg', '.jpeg', '.pdf', '.exe', '.dll', '.zip', '.tar', '.gz'}

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ignore_exts: continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        context_parts.append(f"### {rel_path}\n```\n{content}\n```\n")
                except UnicodeDecodeError:
                    pass # Skip unreadable binary files that slipped through

        return "\n".join(context_parts)

    @staticmethod
    async def extract_and_save_files(chat_id: int, project_name: str, ai_response: str) -> list:
        """
        Parses AI text to find markdown blocks.
        Automatically triggers VCS backups before overwriting.
        Returns a list of saved files.
        """
        # Matches format: ### src/main.py \n ```python \n ... \n ```
        pattern = r'###\s*([a-zA-Z0-9_\-\.\/]+)\s*```[a-zA-Z0-9]*\n(.*?)```'
        matches = re.findall(pattern, ai_response, re.DOTALL)
        
        saved_files = []
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        
        for filepath, code in matches:
            clean_filepath = filepath.strip().lstrip('/').replace('..', '') # Security against directory traversal
            full_path = os.path.join(project_dir, clean_filepath)
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 1. TRIGGER BACKUP (VCS) before overwrite
            await MAGMA_VCS.backup_file_before_edit(chat_id, project_name, clean_filepath, full_path)
            
            # 2. WRITE NEW CODE
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(code.strip())
                
            saved_files.append(clean_filepath)
            
        return saved_files