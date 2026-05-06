import time
import subprocess
import sys
from pathlib import Path
from threading import Event
from typing import Any, Callable

import torch
from PIL import Image

from persona.config.settings import AppConfig
from persona.core.schemas import GenerationResult, output_file_name, sanitize_name
from persona.infra.errors import GenerationCancelled
from persona.infra.pathing import ensure_dir

ProgressCb = Callable[[int, str], None]
PreviewCb = Callable[[str], None]

MAX_PROMPT_TOKENS = 75
NEGATIVE_PROMPT_FIXED = (
    "deformed anatomy, disfigured, malformed face, bad eyes, cross-eyed, bad hands, "
    "extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, artifact, "
    "jpeg artifacts, blurry, lowres, text, watermark, logo, worst quality"
)
IMAGE_STYLE_PREFIXES = {
    "photorealism": "photorealistic portrait, realistic skin texture, natural light",
    "anime": "anime style, clean lineart, cel shading",
    "3d": "3d render, detailed materials, cinematic lighting",
    "illustration": "digital illustration, painterly details, artstation quality",
    "comic": "comic style, inked outlines, stylized shading",
    "fantasy": "fantasy art style, epic atmosphere, dramatic light",
}
FACE_IP_ADAPTER_BIN = "ip-adapter-plus-face_sdxl_vit-h.bin"
FACE_IP_ADAPTER_SAFETENSORS = "ip-adapter-plus-face_sdxl_vit-h.safetensors"
INSIGHTFACE_GIT_URL = "git+https://github.com/deepinsight/insightface.git#subdirectory=python-package"
SINGLE_FILE_MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".pth"}


def _import_diffusers_components() -> tuple[Any, Any, Any, Any]:
    """Importa diffusers en tiempo de uso para evitar fallos al iniciar la UI."""
    try:
        from diffusers import (
            ControlNetModel,
            DPMSolverMultistepScheduler,
            StableDiffusionXLPipeline,
            StableDiffusionXLControlNetPipeline,
        )

        return (
            ControlNetModel,
            StableDiffusionXLPipeline,
            StableDiffusionXLControlNetPipeline,
            DPMSolverMultistepScheduler,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "No se pudo inicializar diffusers en este entorno. "
            "Verifica versiones de PyTorch/diffusers y que el venv esté consistente. "
            f"Detalle: {exc}"
        ) from exc


class GenerationService:
    def __init__(self, config: AppConfig) -> None:
        self._cfg = config

    # -------------------------------------------------------------------------
    def generate(
        self,
        persona_name: str,
        prompt: str,
        cancel_event: Event,
        progress_cb: ProgressCb,
        preview_cb: PreviewCb | None = None,
        base_image_path: str | None = None,
        steps: int | None = None,
        cfg_scale: float | None = None,
        seed: int | None = None,
        seed_mode: str = "fixed",
        width: int | None = None,
        height: int | None = None,
        reference_strength: float = 0.75,
        image_style: str = "photorealism",
        negative_prompt_user: str = "",
        controlnet_enabled: bool = False,
        controlnet_pose_path: str | None = None,
        nsfw_enabled: bool = False,
    ) -> GenerationResult:
        output_dir = ensure_dir(self._cfg.outputs_personas_dir / sanitize_name(persona_name))
        output_path = output_dir / output_file_name(persona_name)
        model_dir = self._resolve_model_dir(nsfw_enabled=nsfw_enabled)

        if cancel_event.is_set():
            raise GenerationCancelled("Generacion cancelada antes de iniciar.")

        pipeline, has_ip_adapters, controlnet_count = self._build_pipeline(
            progress_cb,
            cancel_event,
            base_image_path,
            controlnet_enabled,
            controlnet_pose_path,
            nsfw_enabled,
        )

        device = "cuda" if torch.cuda.is_available() and self._cfg.runtime.device_preference == "cuda" else "cpu"
        progress_cb(55, f"Moviendo pipeline a {device.upper()}...")
        pipeline = pipeline.to(device)

        total_steps = int(steps if steps is not None else self._cfg.runtime.steps)
        preview_path = output_dir / f".preview_{sanitize_name(persona_name)}.jpg"
        preview_every = 3
        guidance_scale = float(
            cfg_scale if cfg_scale is not None else self._cfg.runtime.guidance_scale
        )
        out_width = int(width if width is not None else self._cfg.runtime.width)
        out_height = int(height if height is not None else self._cfg.runtime.height)
        selected_seed = seed if seed is not None else self._cfg.runtime.seed
        seed_mode = "fixed" if selected_seed is not None else "random"
        generator = None
        if selected_seed is not None:
            generator = torch.Generator(device=device).manual_seed(int(selected_seed))

        composed_prompt, prompt_tokens, prompt_truncated = self._compose_prompt(
            pipeline=pipeline,
            image_style=image_style,
            user_prompt=prompt,
            max_tokens=MAX_PROMPT_TOKENS,
        )
        negative_prompt = self._merge_negative_prompts(negative_prompt_user)

        def _step_cb(pipe, step_index, timestep, callback_kwargs):
            if cancel_event.is_set():
                raise GenerationCancelled("Generacion cancelada por el usuario.")
            pct = 55 + int((step_index + 1) / total_steps * 40)
            progress_cb(pct, f"Paso de inferencia {step_index + 1}/{total_steps}...")
            if (
                preview_cb is not None
                and (step_index % preview_every == 0 or step_index == total_steps - 1)
            ):
                latents = callback_kwargs.get("latents")
                if latents is not None:
                    self._emit_preview(
                        pipeline=pipe,
                        latents=latents,
                        preview_path=preview_path,
                        preview_cb=preview_cb,
                    )
            return callback_kwargs

        call_kwargs: dict = dict(
            prompt=composed_prompt,
            negative_prompt=negative_prompt,
            width=out_width,
            height=out_height,
            num_inference_steps=total_steps,
            guidance_scale=guidance_scale,
            callback_on_step_end=_step_cb,
        )
        if generator is not None:
            call_kwargs["generator"] = generator

        if has_ip_adapters and base_image_path and Path(base_image_path).exists():
            progress_cb(56, "Cargando imagen de referencia para IP-Adapter...")
            with Image.open(base_image_path) as ref_img:
                ref_rgb = ref_img.convert("RGB")
                if hasattr(pipeline, "set_ip_adapter_scale"):
                    adapter_count = int(getattr(pipeline, "_persona_ip_adapter_count", 1))
                    if adapter_count > 1:
                        pipeline.set_ip_adapter_scale([float(reference_strength)] * adapter_count)
                    else:
                        pipeline.set_ip_adapter_scale(float(reference_strength))
                if adapter_count > 1:
                    # Diffusers exige una imagen por cada IP-Adapter cargado.
                    call_kwargs["ip_adapter_image"] = [ref_rgb.copy() for _ in range(adapter_count)]
                else:
                    call_kwargs["ip_adapter_image"] = ref_rgb

        control_pose_exists = bool(
            controlnet_enabled and controlnet_pose_path and Path(controlnet_pose_path).exists()
        )
        if controlnet_count > 0 and control_pose_exists:
            progress_cb(57, "Aplicando pose seleccionada para ControlNet...")
            with Image.open(str(controlnet_pose_path)) as pose_img:
                pose_rgb = pose_img.convert("RGB")
                if controlnet_count == 1:
                    call_kwargs["image"] = pose_rgb
                    call_kwargs["controlnet_conditioning_scale"] = float(reference_strength)
                else:
                    call_kwargs["image"] = [pose_rgb] * controlnet_count
                    call_kwargs["controlnet_conditioning_scale"] = [
                        float(reference_strength)
                    ] * controlnet_count

        progress_cb(57, "Iniciando inferencia...")
        try:
            result = pipeline(**call_kwargs)
        finally:
            del pipeline
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        if cancel_event.is_set():
            raise GenerationCancelled("Generacion cancelada por el usuario.")

        progress_cb(96, "Guardando imagen...")
        result.images[0].save(output_path)
        if preview_path.exists():
            try:
                preview_path.unlink()
            except OSError:
                pass
        progress_cb(100, f"Imagen generada: {output_path.name}")
        metadata = {
            "device": device,
            "dtype": self._cfg.runtime.dtype,
            "width": out_width,
            "height": out_height,
            "steps": total_steps,
            "guidance_scale": guidance_scale,
            "seed": int(selected_seed) if selected_seed is not None else None,
            "seed_mode": seed_mode,
            "sampler": "DPM++ 2M SDE",
            "schedule_type": "Exponential",
            "image_style": image_style,
            "prompt_composed": composed_prompt,
            "prompt_token_count": prompt_tokens,
            "prompt_truncated": prompt_truncated,
            "negative_prompt_fixed": NEGATIVE_PROMPT_FIXED,
            "negative_prompt_user": negative_prompt_user.strip(),
            "reference_strength": float(reference_strength),
            "used_base_image": bool(base_image_path and Path(base_image_path).exists()),
            "used_ip_adapter": has_ip_adapters,
            "controlnet_enabled": bool(controlnet_enabled),
            "controlnet_pose_path": controlnet_pose_path,
            "used_controlnet": controlnet_count > 0,
            "nsfw_enabled": bool(nsfw_enabled),
            "model_variant": "nsfw" if nsfw_enabled else "sfw",
            "model_path": str(model_dir),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return GenerationResult(output_path=output_path, metadata=metadata)

    # -------------------------------------------------------------------------
    def _merge_negative_prompts(self, negative_prompt_user: str) -> str:
        user = (negative_prompt_user or "").strip()
        runtime_base = (self._cfg.runtime.negative_prompt or "").strip()
        parts = [NEGATIVE_PROMPT_FIXED]
        if runtime_base:
            parts.append(runtime_base)
        if user:
            parts.append(user)
        return ", ".join(parts)

    # -------------------------------------------------------------------------
    def _compose_prompt(
        self,
        pipeline,
        image_style: str,
        user_prompt: str,
        max_tokens: int,
    ) -> tuple[str, int, bool]:
        style_key = (image_style or "photorealism").strip().lower()
        style_prefix = IMAGE_STYLE_PREFIXES.get(style_key, IMAGE_STYLE_PREFIXES["photorealism"])
        composed = f"style: {style_prefix}. {user_prompt.strip()}".strip()
        return self._truncate_to_tokens(pipeline, composed, max_tokens)

    # -------------------------------------------------------------------------
    def _truncate_to_tokens(
        self,
        pipeline,
        text: str,
        max_tokens: int,
    ) -> tuple[str, int, bool]:
        tokenizer = getattr(pipeline, "tokenizer_2", None) or getattr(pipeline, "tokenizer", None)
        if tokenizer is None:
            words = text.split()
            if len(words) <= max_tokens:
                return text, len(words), False
            return " ".join(words[:max_tokens]), max_tokens, True

        token_ids = tokenizer(text, add_special_tokens=False).input_ids
        token_count = len(token_ids)
        if token_count <= max_tokens:
            return text, token_count, False

        trimmed_ids = token_ids[:max_tokens]
        truncated = tokenizer.decode(
            trimmed_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()
        return truncated, max_tokens, True

    # -------------------------------------------------------------------------
    def _emit_preview(
        self,
        pipeline,
        latents,
        preview_path: Path,
        preview_cb: PreviewCb,
    ) -> None:
        try:
            with torch.no_grad():
                scale = getattr(pipeline.vae.config, "scaling_factor", 0.18215)
                decoded = pipeline.vae.decode(latents / scale, return_dict=False)[0]
                image = (decoded / 2 + 0.5).clamp(0, 1)
                image = image.detach().cpu().permute(0, 2, 3, 1).float().numpy()
                pil_preview = pipeline.numpy_to_pil(image)[0]
                pil_preview.save(preview_path, format="JPEG", quality=75)
            preview_cb(str(preview_path))
        except Exception:
            # La preview es best-effort; no debe romper la generación principal.
            return

    # -------------------------------------------------------------------------
    def _build_pipeline(
        self,
        progress_cb: ProgressCb,
        cancel_event: Event,
        base_image_path: str | None = None,
        controlnet_enabled: bool = False,
        controlnet_pose_path: str | None = None,
        nsfw_enabled: bool = False,
    ) -> tuple:
        (
            control_net_model_cls,
            sdxl_pipeline_cls,
            sdxl_controlnet_pipeline_cls,
            dpm_scheduler_cls,
        ) = (
            _import_diffusers_components()
        )

        model_source, model_load_mode = self._resolve_model_source(nsfw_enabled=nsfw_enabled)

        if not model_source.exists():
            variant_label = "NSFW" if nsfw_enabled else "base"
            raise RuntimeError(
                f"No se encontro el modelo {variant_label} SDXL en ruta local:\n"
                f"  {model_source}\n"
                "Configura la ruta en config_persona.json y vuelve a intentar."
            )

        dtype = (
            torch.float16
            if self._cfg.runtime.dtype == "float16" and torch.cuda.is_available()
            else torch.float32
        )

        has_ref = bool(base_image_path and Path(base_image_path).exists())
        has_controlnet_pose = bool(
            controlnet_enabled and controlnet_pose_path and Path(controlnet_pose_path).exists()
        )

        # ControlNet solo cuando se activa y hay pose seleccionada.
        controlnet = None
        if has_controlnet_pose:
            controlnet = self._load_controlnets(control_net_model_cls, dtype, progress_cb)

        if cancel_event.is_set():
            raise GenerationCancelled("Cancelado durante carga de modelos.")

        variant_label = "NSFW" if nsfw_enabled else "base"
        progress_cb(20, f"Cargando modelo {variant_label}: {model_source.name} ({model_load_mode})...")
        if model_load_mode == "single_file":
            if controlnet is not None:
                pipeline = sdxl_controlnet_pipeline_cls.from_single_file(
                    str(model_source),
                    torch_dtype=dtype,
                    local_files_only=True,
                    controlnet=controlnet,
                )
            else:
                pipeline = sdxl_pipeline_cls.from_single_file(
                    str(model_source),
                    torch_dtype=dtype,
                    local_files_only=True,
                )
        else:
            if controlnet is not None:
                pipeline = sdxl_controlnet_pipeline_cls.from_pretrained(
                    str(model_source),
                    torch_dtype=dtype,
                    local_files_only=True,
                    controlnet=controlnet,
                )
            else:
                pipeline = sdxl_pipeline_cls.from_pretrained(
                    str(model_source),
                    torch_dtype=dtype,
                    local_files_only=True,
                )

        if cancel_event.is_set():
            raise GenerationCancelled("Cancelado durante carga del modelo base.")

        # Sampler fijo requerido: DPM++ 2M SDE + scheduler exponencial.
        try:
            pipeline.scheduler = dpm_scheduler_cls.from_config(
                pipeline.scheduler.config,
                algorithm_type="sde-dpmsolver++",
                use_exponential_sigmas=True,
            )
        except TypeError:
            pipeline.scheduler = dpm_scheduler_cls.from_config(
                pipeline.scheduler.config,
                algorithm_type="sde-dpmsolver++",
            )

        has_ip_adapters = False
        # En algunos stacks SDXL, combinar ControlNet + IP-Adapter puede romper dimensiones en runtime.
        # Priorizamos ControlNet cuando hay referencia para mantener generación estable.
        if has_ref and controlnet is None:
            self._ensure_insightface_installed(progress_cb)
            has_ip_adapters = self._attach_ip_adapters(pipeline, progress_cb)

        if controlnet is None:
            controlnet_count = 0
        elif isinstance(controlnet, list):
            controlnet_count = len(controlnet)
        else:
            controlnet_count = 1

        return pipeline, has_ip_adapters, controlnet_count

    # -------------------------------------------------------------------------
    def _resolve_model_dir(self, nsfw_enabled: bool) -> Path:
        if nsfw_enabled:
            if self._cfg.models.sdxl_nsfw_path is None:
                raise RuntimeError(
                    "NSFW activado, pero no hay ruta de modelo NSFW configurada en config_persona.json."
                )
            return self._cfg.models.sdxl_nsfw_path
        return self._cfg.models.sdxl_base_path

    # -------------------------------------------------------------------------
    def _resolve_model_source(self, nsfw_enabled: bool) -> tuple[Path, str]:
        model_path = self._resolve_model_dir(nsfw_enabled=nsfw_enabled)
        if model_path.is_file():
            if model_path.suffix.lower() in SINGLE_FILE_MODEL_EXTENSIONS:
                return model_path, "single_file"
            raise RuntimeError(
                "La ruta de modelo apunta a un archivo no compatible. "
                "Usa una carpeta Diffusers o un checkpoint .safetensors/.ckpt/.pt/.pth.\n"
                f"Ruta: {model_path}"
            )

        if model_path.is_dir():
            if (model_path / "model_index.json").exists():
                return model_path, "diffusers_dir"

            single_file_candidates = sorted(
                [
                    candidate
                    for candidate in model_path.iterdir()
                    if candidate.is_file() and candidate.suffix.lower() in SINGLE_FILE_MODEL_EXTENSIONS
                ]
            )
            if single_file_candidates:
                return single_file_candidates[0], "single_file"

            raise RuntimeError(
                "La carpeta del modelo existe pero no contiene un modelo cargable.\n"
                "Debe incluir model_index.json (formato Diffusers) o un checkpoint .safetensors/.ckpt/.pt/.pth.\n"
                f"Ruta: {model_path}"
            )

        return model_path, "diffusers_dir"

    # -------------------------------------------------------------------------
    def _load_controlnets(self, control_net_model_cls: Any, dtype, progress_cb: ProgressCb):
        existing = [p for p in self._cfg.models.controlnet_paths if p.exists()]
        if not existing:
            return None
        models = []
        for i, path in enumerate(existing):
            progress_cb(5 + i * 5, f"Cargando ControlNet {i + 1}/{len(existing)}: {path.name}...")
            models.append(
                control_net_model_cls.from_pretrained(
                    str(path), torch_dtype=dtype, local_files_only=True
                )
            )
        return models[0] if len(models) == 1 else models

    # -------------------------------------------------------------------------
    def _ensure_insightface_installed(self, progress_cb: ProgressCb) -> None:
        try:
            import insightface  # noqa: F401

            return
        except Exception:
            progress_cb(34, "InsightFace no encontrado. Instalando desde GitHub...")

        install_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            INSIGHTFACE_GIT_URL,
        ]
        result = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            detail = "\n".join(detail.splitlines()[-12:])
            raise RuntimeError(
                "No se pudo instalar InsightFace desde el repositorio oficial.\n"
                f"Comando: {' '.join(install_cmd)}\n"
                f"Detalle:\n{detail}"
            )

        try:
            import insightface  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "InsightFace se instalo, pero no pudo importarse correctamente. "
                f"Detalle: {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    def _attach_ip_adapters(self, pipeline, progress_cb: ProgressCb) -> bool:
        if not hasattr(pipeline, "load_ip_adapter"):
            return False

        face_root = self._cfg.models.ip_adapter_paths.get("face")
        if face_root is None or not face_root.exists():
            return False

        subfolder = self._cfg.models.ip_adapter_subfolders.get("face", "sdxl_models")
        adapter_dir = face_root / subfolder if subfolder else face_root
        if not adapter_dir.exists():
            return False

        configured_weight = self._cfg.models.ip_adapter_weights.get(
            "face", FACE_IP_ADAPTER_SAFETENSORS
        )
        candidate_weights = [
            configured_weight,
            FACE_IP_ADAPTER_SAFETENSORS,
            FACE_IP_ADAPTER_BIN,
        ]
        selected_weight = next(
            (name for name in candidate_weights if name and (adapter_dir / name).exists()),
            None,
        )
        if selected_weight is None:
            return False

        # Para pesos vit-h, diffusers debe usar el encoder ViT-H (1280), no bigG (1664).
        image_encoder_folder = "models/image_encoder" if "vit-h" in selected_weight else None

        progress_cb(40, "Cargando IP-Adapter Face SDXL (vit-h)...")
        try:
            kwargs: dict[str, Any] = {
                "local_files_only": True,
                "subfolder": subfolder,
                "weight_name": selected_weight,
            }
            if image_encoder_folder:
                kwargs["image_encoder_folder"] = image_encoder_folder

            pipeline.load_ip_adapter(str(face_root), **kwargs)
            setattr(pipeline, "_persona_ip_adapter_count", 1)
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------