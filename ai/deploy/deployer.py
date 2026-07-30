import os
import asyncssh
import asyncio
from config import Config
from utils.logger import logger

class VPSDeployer:
    def __init__(self, host: str, username: str, password: str = None, key_path: str = None):
        self.host = host
        self.username = username
        self.password = password
        self.key_path = key_path

    async def _create_dockerfile_if_missing(self, project_dir: str):
        """Automatically generates a basic Python Dockerfile if AI didn't create one."""
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            with open(dockerfile_path, "w") as f:
                f.write("""FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
CMD ["python", "main.py"]
""")
            logger.info("[Deployer] Auto-generated Dockerfile.")

    async def deploy_project(self, project_name: str, port: int = 8080) -> str:
        """Uploads project to VPS and spins up a Docker container."""
        project_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        remote_dir = f"/var/www/magma_{project_name}"
        
        await self._create_dockerfile_if_missing(project_dir)
        
        connect_kwargs = {"username": self.username}
        if self.password: connect_kwargs["password"] = self.password
        if self.key_path: connect_kwargs["client_keys"] = [self.key_path]

        try:
            logger.info(f"[Deployer] Connecting to VPS: {self.host}...")
            async with asyncssh.connect(self.host, **connect_kwargs) as conn:
                
                # 1. Prepare Remote Directory
                await conn.run(f"mkdir -p {remote_dir}")
                
                # 2. Upload Files (Using SFTP)
                logger.info(f"[Deployer] Uploading files to {remote_dir}...")
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(project_dir, remote_dir, recurse=True)

                # 3. Build Docker Image
                logger.info(f"[Deployer] Building Docker Image for {project_name}...")
                build_cmd = f"cd {remote_dir}/{project_name} && docker build -t {project_name}_img ."
                result = await conn.run(build_cmd, check=True)

                # 4. Stop old container if exists, then Run new one
                logger.info("[Deployer] Starting Live Container...")
                await conn.run(f"docker stop {project_name}_app || true")
                await conn.run(f"docker rm {project_name}_app || true")
                
                run_cmd = f"docker run -d --name {project_name}_app -p {port}:8080 {project_name}_img"
                await conn.run(run_cmd, check=True)

                return f"✅ **Successfully Deployed!**\nLive URL: `http://{self.host}:{port}`"
                
        except Exception as e:
            logger.error(f"[Deployer] Deployment Failed: {e}")
            return f"❌ **Deployment Failed:**\n`{str(e)}`"