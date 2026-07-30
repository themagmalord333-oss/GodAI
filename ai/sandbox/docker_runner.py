import docker
import asyncio
import os
from config import Config
from utils.logger import logger

class SecureDockerSandbox:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"[Sandbox] Docker daemon not running: {e}")
            self.client = None

    def _run_container_sync(self, entry_point: str) -> dict:
        """Synchronous docker execution (wrapped in async later)"""
        if not self.client:
            return {"status": "error", "exit_code": -1, "logs": "Docker is not running on the host server."}

        # Ensure directory exists
        if not os.path.exists(self.project_dir):
            return {"status": "error", "exit_code": -1, "logs": "Project directory missing."}

        try:
            # We mount the project dir to /app inside the container
            container = self.client.containers.run(
                image="python:3.10-slim",
                command=f"python {entry_point}",
                volumes={os.path.abspath(self.project_dir): {'bind': '/app', 'mode': 'rw'}},
                working_dir="/app",
                detach=True,
                mem_limit="256m",       # RAM Limit
                nano_cpus=500000000,    # 0.5 CPU Core Limit
                network_disabled=True,  # No internet access during test (Security)
                remove=True             # Auto-cleanup container after run
            )

            # Wait for execution with a strict 30-second timeout
            result = container.wait(timeout=30)
            exit_code = result.get('StatusCode', 1)
            
            # Fetch stdout & stderr
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            return {
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "logs": logs[-2000:] # Keep last 2000 chars to avoid prompt bloat
            }
            
        except docker.errors.ContainerError as e:
            return {"status": "failed", "exit_code": e.exit_status, "logs": e.stderr.decode('utf-8')[-2000:]}
        except Exception as e:
            logger.error(f"[Sandbox Error] {e}")
            return {"status": "error", "exit_code": -1, "logs": str(e)}

    async def execute(self, entry_point: str = "main.py") -> dict:
        """Asynchronous wrapper for Docker execution."""
        logger.info(f"[Sandbox] Starting test for {self.project_name}/{entry_point}")
        return await asyncio.to_thread(self._run_container_sync, entry_point)