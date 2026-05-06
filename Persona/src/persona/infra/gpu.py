from dataclasses import dataclass

import torch


@dataclass(slots=True)
class GPUStatus:
    cuda_available: bool
    gpu_name: str
    torch_version: str
    cuda_runtime: str
    capability: str
    warning: str | None = None


def evaluate_runtime_gpu() -> GPUStatus:
    torch_version = torch.__version__
    cuda_runtime = torch.version.cuda or "none"

    if not torch.cuda.is_available():
        return GPUStatus(
            cuda_available=False,
            gpu_name="CPU",
            torch_version=torch_version,
            cuda_runtime=cuda_runtime,
            capability="none",
            warning="CUDA no disponible en runtime.",
        )

    index = torch.cuda.current_device()
    gpu_name = torch.cuda.get_device_name(index)
    major, minor = torch.cuda.get_device_capability(index)
    capability = f"{major}.{minor}"

    warning = None
    if major < 8:
        warning = "GPU detectada con compute capability antiguo; revisar rendimiento y soporte."

    return GPUStatus(
        cuda_available=True,
        gpu_name=gpu_name,
        torch_version=torch_version,
        cuda_runtime=cuda_runtime,
        capability=capability,
        warning=warning,
    )
