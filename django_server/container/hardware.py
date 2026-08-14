"""Host RAM/VRAM detection for the "which model fits my machine" feature.

RAM comes from the Docker SDK (`client.info()["MemTotal"]`) — on Docker
Desktop this is the memory allocated to the Docker VM, which is actually the
more relevant number than raw host RAM for "will this fit in a container".
VRAM has no Docker SDK equivalent; nvidia-smi is the only reasonably
portable way to read it without a vendor SDK, so non-NVIDIA machines (AMD,
Apple Silicon, CPU-only) get None rather than a guess.
"""

import logging
import shutil
import subprocess

from .ContainerManager import ContainerManager

logger = logging.getLogger(__name__)

NVIDIA_SMI_TIMEOUT_SECONDS = 5


def get_host_ram_bytes(container_manager: ContainerManager) -> int | None:
    if container_manager.client is None:
        return None

    try:
        return container_manager.client.info().get("MemTotal")
    except Exception as e:
        logger.warning("Could not read host RAM from Docker: %s", e)
        return None


def get_gpu_vram_bytes() -> int | None:
    if shutil.which("nvidia-smi") is None:
        return None

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=NVIDIA_SMI_TIMEOUT_SECONDS,
            check=True,
        )
        first_line = result.stdout.strip().splitlines()[0]
        return int(first_line) * 1024 * 1024  # nvidia-smi reports MiB
    except Exception as e:
        logger.warning("Could not read GPU VRAM via nvidia-smi: %s", e)
        return None
