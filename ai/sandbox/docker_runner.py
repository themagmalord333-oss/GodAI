import docker
import asyncio
import os
from config.config import Config
from utils.logger import logger

class SecureDockerSandbox:
    def __init__(self, project_name: str):
        self.project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def _run_container_sync(self, entry_point: str) -> dict:
        if not self.client: return {"status": "error", "logs": "Docker daemon not running."}
        try:
            container = self.client.containers.run(
                image="python:3.10-slim",
                command=f"python {entry_point}",
                volumes={os.path.abspath(self.project_dir): {'bind': '/app', 'mode': 'rw'}},
                working_dir="/app",
                detach=True, mem_limit="256m", network_disabled=True, remove=True
            )
            result = container.wait(timeout=30)
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            return {"status": "success" if result.get('StatusCode', 1) == 0 else "failed", "logs": logs[-1000:]}
        except Exception as e:
            return {"status": "error", "logs": str(e)}

    async def execute(self, entry_point: str = "main.py") -> dict:
        return await asyncio.to_thread(self._run_container_sync, entry_point)