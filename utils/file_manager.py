import os
import re
import aiofiles
from config.config import Config
from utils.vcs import MAGMA_VCS

class FileManager:
    @staticmethod
    async def read_project_context(project_name: str) -> str:
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        if not os.path.exists(project_dir): return "No existing files."
        context_parts = ["CURRENT PROJECT STATE:\n"]
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv', 'node_modules'}]
            for file in files:
                if file.endswith(('.png', '.jpg', '.pdf', '.exe', '.zip')): continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        context_parts.append(f"### {rel_path}\n```\n{content}\n```\n")
                except: pass
        return "\n".join(context_parts)

    @staticmethod
    async def extract_and_save_files(chat_id: int, project_name: str, ai_response: str) -> list:
        pattern = r'###\s*([a-zA-Z0-9_\-\.\/]+)\s*```[a-zA-Z0-9]*\n(.*?)```'
        matches = re.findall(pattern, ai_response, re.DOTALL)
        saved_files = []
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        for filepath, code in matches:
            clean_filepath = filepath.strip().lstrip('/').replace('..', '')
            full_path = os.path.join(project_dir, clean_filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            await MAGMA_VCS.backup_file_before_edit(chat_id, project_name, clean_filepath, full_path)
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(code.strip())
            saved_files.append(clean_filepath)
        return saved_files