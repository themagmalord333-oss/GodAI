import os
import asyncssh
import asyncio
from config.config import Config
from utils.logger import logger

class VPSDeployer:
    def __init__(self, host: str, username: str, password: str = None, key_path: str = None):
        self.host = host
        self.username = username
        self.password = password
        self.key_path = key_path

    async def deploy_project(self, project_name: str, port: int = 8080) -> str:
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        remote_dir = f"/var/www/anysnap_{project_name}"
        
        # Auto-create basic Dockerfile if missing
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            with open(dockerfile_path, "w") as f:
                f.write("FROM python:3.10-slim\nWORKDIR /app\nCOPY . /app\nRUN pip install -r requirements.txt || true\nCMD [\"python\", \"main.py\"]")

        connect_kwargs = {"username": self.username}
        if self.password: connect_kwargs["password"] = self.password
        if self.key_path: connect_kwargs["client_keys"] = [self.key_path]

        try:
            logger.info(f"[Deployer] Connecting to VPS: {self.host}...")
            async with asyncssh.connect(self.host, **connect_kwargs) as conn:
                await conn.run(f"mkdir -p {remote_dir}")
                
                # Upload files via SFTP
                logger.info("[Deployer] Uploading files...")
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(project_dir, remote_dir, recurse=True)

                # Build & Run Docker on remote VPS
                logger.info("[Deployer] Building remote Docker Image...")
                await conn.run(f"cd {remote_dir} && docker build -t {project_name}_img .", check=True)
                
                await conn.run(f"docker stop {project_name}_app || true")
                await conn.run(f"docker rm {project_name}_app || true")
                await conn.run(f"docker run -d --name {project_name}_app -p {port}:8080 {project_name}_img", check=True)

                return f"✅ **Successfully Deployed!**\nYour App is live on your VPS."
                
        except Exception as e:
            logger.error(f"[Deployer] Failed: {e}")
            return f"❌ **Deployment Failed:**\n`{str(e)}`"