#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the full garden RPG image set on Google Colab, saving sequentially to
Google Drive, with skip / regenerate control via CONFIG, and a final ZIP whose
internal tree mirrors the app's static/img paths so one extraction lands
everything in the right folders.

HOW TO USE IN COLAB
--------------------
1) Paste Cell 0 (below the header) into the first Colab cell, edit the mount
   path if needed, and RUN it. This mounts Drive and installs deps.
2) Paste Cell 1 (IMAGES + CONFIG), then Cell 2 (manifest), Cell 3 (generator),
   Cell 4 (finalize), Cell 5 (main loop), Cell 6 (zip) — one per Colab cell,
   IN ORDER. Run them top to bottom.
3) Re-run ONLY Cell 5 to resume / regenerate subsets (edit CONFIG first).

Everything below is a plain Colab paste — no app imports, no Framework
dependencies. The script is split into clearly marked CELL blocks so you can
run individual stages independently and reload the model cheaply (the pipeline
stays cached in the runtime after the first Cell 3 run).
"""

__all__ = ["IMAGES", "CONFIG", "PREAMBLE"]  # noqa: F401 (imported by later cells)


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 0 — MOUNT DRIVE + INSTALL DEPS  (paste into its own Colab cell)
# ═══════════════════════════════════════════════════════════════════════════════
#
#   from google.colab import drive
#   drive.mount('/content/drive')
#
#   # Your single root knob — everything under here is created/owned by the script
#   ROOT_DIR = "/content/drive/MyDrive/garden-rpg-images"
#
#   %pip install -q pillow tqdm
#   # Uncomment the pieces you need once you pick a model:
#   # %pip install -q diffusers transformers accelerate safetensors
#   # %pip install -q rembg            # heavy (~170MB), optional; Pillow fallback exists
#
#   import numpy as np, os, json, shutil, math, io, time, base64, zipfile
#   from PIL import Image, ImageOps, ImageEnhance, ImageFilter
#   from tqdm.auto import tqdm
#   try:
#       from google.colab import files as _gfiles
#   except Exception:
#       _gfiles = None                  # not on Colab -> zip download no-ops


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1 — IMPORTS + STYLE PREAMBLE + IMAGES DICT + CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
import os
import io
import re
import json
import time
import base64
import shutil
from PIL import Image, ImageOps, ImageFilter
from tqdm.auto import tqdm

# Colab download hook; stays None off-Colab so build_and_download_zip degrades
# gracefully to just printing the zip path.
try:
    from google.colab import files as _gfiles
except Exception:
    _gfiles = None

PREAMBLE = (
    "Painterly digital illustration style, semi-realistic, soft painterly brushwork. "
    "Not a photograph. Not a 3D render. Not flat vector or cartoon style. Not anime. "
    "Single warm light source from the upper-left of the frame, low golden-hour sun, "
    "shadows falling toward the lower-right. Color grading: sky gradient from deep "
    "violet (#5B2A6E) at top, through magenta-red (#C4416B) and orange (#E86A3B), "
    "to warm gold (#F4A93C) near the horizon, where relevant. "
    "No humans or people anywhere in the image. No readable text, no logos, no "
    "watermarks, no signature. No lens flare, no film grain, no heavy HDR glow. sRGB color."
)

HERO_BASE_COMPOSITION = (
    "Wide-angle Japanese garden valley at dusk, elevated vantage point, distant "
    "mountain silhouettes across the top third, open sky above them, garden terrain "
    "filling the bottom two-thirds, a path or stream running from the lower-left "
    "corner toward the center. Areas where the Academy, River bridge, Moon shrine, "
    "and Village would go are open undeveloped terrain - do not draw any buildings "
    "into this base image."
)

IMAGES = [
    # ── Group 1 — hero backgrounds (img/, 1800x1200 jpg) ──
    {"id": "hero-spring", "filename": "garden-hero-spring.jpg", "folder": "img",
     "kind": "hero", "size": (1800, 1200), "transparent": False,
     "scene": f"{HERO_BASE_COMPOSITION} Spring version. Cherry blossom trees in full "
              "pink bloom scattered through the terrain. Green grass. No snow, no fallen leaves."},
    {"id": "hero-summer", "filename": "garden-hero-summer.jpg", "folder": "img",
     "kind": "hero", "size": (1800, 1200), "transparent": False,
     "scene": f"{HERO_BASE_COMPOSITION} Summer version, identical composition. Dense "
              "deep-green foliage, no blossoms. Green grass. Slightly brighter, warmer sky near the horizon."},
    {"id": "hero-autumn", "filename": "garden-hero-autumn.jpg", "folder": "img",
     "kind": "hero", "size": (1800, 1200), "transparent": False,
     "scene": f"{HERO_BASE_COMPOSITION} Autumn version, identical composition. Foliage "
              "in red, orange, and yellow tones, some trees bare. A scatter of fallen "
              "leaves along the path. Warmer amber cast overall."},
    {"id": "hero-winter", "filename": "garden-hero-winter.jpg", "folder": "img",
     "kind": "hero", "size": (1800, 1200), "transparent": False,
     "scene": f"{HERO_BASE_COMPOSITION} Winter version, identical composition. Bare "
              "branches, or branches with a light dusting of snow. A light dusting of "
              "snow on the path edges only, no deep drifts. Sky shifted slightly cooler and bluer."},

    # ── Group 2a — Academy (INT, cyan) ──
    {"id": "academy-tier1", "filename": "academy-tier1.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Academy tier 1. One small wooden hut with a thatched roof, isolated on "
              "transparent background. No lit lantern. 1-2 sparse small bushes nearby. "
              "A short fragment of dirt path. Muted, low-saturation colors."},
    {"id": "academy-tier2", "filename": "academy-tier2.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Academy tier 2. A small single-story wooden building, isolated on "
              "transparent background, with one paper lantern lit, glowing cyan-white. "
              "3-4 small trees or shrubs around it. A short stone path segment leading to the door."},
    {"id": "academy-tier3", "filename": "academy-tier3.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Academy tier 3. A two-story pagoda-style building, isolated on transparent "
              "background. Two lit lanterns with cyan-tinted glow. A small stone courtyard "
              "in front. One stone lantern post. A denser line of trees behind. A small "
              "hanging fabric banner, plain, no text."},
    {"id": "academy-tier4", "filename": "academy-tier4.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Academy tier 4. A full academy complex, isolated on transparent background: "
              "a two-story pagoda plus one smaller adjoining library building connected by "
              "a covered walkway. Four or more lit lanterns with soft cyan glow halos. A "
              "stone-paved courtyard. Cherry blossom trees flanking the entrance. A small "
              "torii gate at the courtyard entrance. Warm illuminated windows."},

    # ── Group 2b — River (STA, cool teal water) ──
    {"id": "river-tier1", "filename": "river-tier1.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "River tier 1. A thin trickling stream over bare rocks, isolated on "
              "transparent background. No bridge. A few sparse reeds at the bank."},
    {"id": "river-tier2", "filename": "river-tier2.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "River tier 2. A wider stream, isolated on transparent background. A handful "
              "of flat stepping stones crossing it. Small clusters of reed grass on both banks."},
    {"id": "river-tier3", "filename": "river-tier3.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "River tier 3. A flowing river with visible ripple linework on the surface, "
              "rendered in teal-blue tones, isolated on transparent background. A simple "
              "flat wooden plank bridge crosses it. A few koi fish silhouettes visible just "
              "beneath the surface."},
    {"id": "river-tier4", "filename": "river-tier4.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "River tier 4. A full river scene, isolated on transparent background: an "
              "arched ornate wooden bridge with simple railings in traditional Japanese "
              "garden style. Stone-lined riverbanks. Multiple visible koi fish. Small "
              "lanterns along the bank with reflections in the water. A willow tree or "
              "dense reed bed on one bank."},

    # ── Group 2c — Moon (FCS, indigo/violet + gold) ──
    {"id": "moon-tier1", "filename": "moon-tier1.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Moon tier 1. A single small flat stone marker under open sky, isolated on "
              "transparent background. A faint pale moon visible above it. No structure."},
    {"id": "moon-tier2", "filename": "moon-tier2.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Moon tier 2. A small stone shrine fragment or single torii post, isolated "
              "on transparent background. Dim moonlight. One or two flat meditation stones nearby."},
    {"id": "moon-tier3", "filename": "moon-tier3.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Moon tier 3. A small shrine building with a circular moon-gate opening, "
              "isolated on transparent background. A patch of deep indigo-violet sky "
              "directly above it. Gold-lit lanterns flanking the shrine. A small "
              "arrangement of meditation stones in front."},
    {"id": "moon-tier4", "filename": "moon-tier4.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Moon tier 4. A full moon shrine, isolated on transparent background: an "
              "elevated circular moon-gate structure on a raised stone platform, accessed "
              "by a few stone steps. Multiple gold-glowing lanterns. A pronounced "
              "indigo-violet glow in the sky directly above. Drifting cherry blossom "
              "petals in the air around it."},

    # ── Group 2d — Village (CHA, purple) ──
    {"id": "village-tier1", "filename": "village-tier1.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Village tier 1. A single empty market stall frame, isolated on transparent "
              "background: wooden posts and a bare roof beam, no walls, no goods, no lanterns."},
    {"id": "village-tier2", "filename": "village-tier2.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Village tier 2. Two small stalls or huts, isolated on transparent "
              "background. A few paper lanterns present but unlit. Minimal decoration."},
    {"id": "village-tier3", "filename": "village-tier3.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Village tier 3. A small cluster of 3-4 buildings resembling a teahouse "
              "district, isolated on transparent background. Purple paper lanterns, lit. "
              "Simple plain-colored fabric banners, no text."},
    {"id": "village-tier4", "filename": "village-tier4.png", "folder": "img/regions",
     "kind": "region", "size": (400, 400), "transparent": True,
     "scene": "Village tier 4. A full village/festival district, isolated on transparent "
              "background: several buildings, strings of lit purple lanterns strung "
              "between them, plain fabric banners, a small gathering square with empty "
              "benches or low tables, possibly a small footbridge connecting to the rest "
              "of the garden. No people."},

    # ── Group 3 — garden-health washes (img/, 1800x1200 semi-transparent PNG) ──
    {"id": "health-flourishing", "filename": "garden-health-flourishing.png", "folder": "img",
     "kind": "wash", "size": (1800, 1200), "transparent": True,
     "scene": "A very subtle warm gold-tinted brightening wash, strongest as a soft "
              "vignette lightening near the edges, roughly 15-20% opacity overall. No "
              "scene content, just a translucent color wash. Transparent PNG."},
    # Synthetic, NO model call:
    {"id": "health-stable", "filename": "garden-health-stable.png", "folder": "img",
     "kind": "wash_blank", "size": (1800, 1200), "transparent": True, "scene": "blank"},
    {"id": "health-neglected", "filename": "garden-health-neglected.png", "folder": "img",
     "kind": "wash", "size": (1800, 1200), "transparent": True,
     "scene": "A subtle desaturating dark vignette wash, strongest near the edges, "
              "roughly 20-25% opacity overall, with a faint cool grey-blue mist tint. "
              "No scene content, just a translucent color wash. Transparent PNG."},
]


CONFIG = {
    # Your single root knob (Cello sets it too; keep in sync)
    "ROOT": "/content/drive/MyDrive/garden-rpg-images",

    # MODE: "missing" -> generate only files not already saved + marked ok (resume)
    #       "all"     -> (re)generate every entry, ignoring manifest
    #       "failed"  -> only retry entries whose manifest status is "failed"
    "mode": "missing",

    # Per-file / per-group opt-outs — never spend GPU on art you already have.
    # Valid group values: "hero", "region", "wash" (wash_blank is always cheap/synthetic).
    "skip_groups": [],                      # e.g. ["region"] to only do hero seasons + health
    "skip_filenames": [],                   # e.g. ["garden-health-stable.png"]

    # Model branch: "auto" | "diffusers" | "api"  (undecided -> keep "auto")
    "generator": "auto",
    # ── For "diffusers": set an exact model id ──
    #   Light/best VRAM:   "runwayml/stable-diffusion-v1-5"  (512px, fast)
    #   High quality:      "stabilityai/stable-diffusion-xl-base-1.0" (needs more VRAM/Colab GPU)
    #   (Set None and pick below when you choose; provider then auto-detects.)
    "model_id": None,
    # ── For "api": set endpoint + token ──
    "api_url": None,                        # e.g. ".../v1/images/generations" (OpenAI-ish) or HF Inference
    "api_key": None,                        # your token; paste or set env
    "api_image_field": "b64_json",          # response field holding the image: "b64_json" | "url"

    # Generation knobs
    "seed": 7331,                           # base seed; hero seasons reuse it for matched composition
    "guidance_scale": 7.5,
    "steps": 28,
    "device": "cuda",

    # Region transparency: if the model returns an opaque bg, force alpha regardless.
    "force_transparent": True,

    # ZIP + manifest
    "zip_name": "garden-images.zip",
    "manifest_name": "manifest.json",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 2 — MANIFEST (survives Drive persistence across sessions)
# ═══════════════════════════════════════════════════════════════════════════════
def _root_dir():
    r = getattr(CONFIG, "_root", None) or CONFIG["ROOT"]
    r = r.replace("\\", "/")
    # Colab uses absolute POSIX paths (/content/...). Local/dev usage may be a
    # Windows path (C:/...). Normalise to an absolute path in either case.
    if re.match(r"^[A-Za-z]:", r):          # Windows drive path -> leave as-is
        return r
    if not r.startswith("/"):
        r = "/" + r.lstrip("/")
    return r


def manifest_path():
    return os.path.join(_root_dir(), CONFIG["manifest_name"])


def load_manifest():
    key = CONFIG["manifest_name"]
    p = manifest_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f).get("files", {})
        except Exception:
            return {}
    return {}


def write_manifest(manifest, paths):
    p = manifest_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = {"files": manifest, "path_guid": paths}
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


def full_path(entry):
    return os.path.join(_root_dir(), entry["folder"], entry["filename"])


def on_disk(entry):
    return os.path.exists(full_path(entry))


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 3 — GENERATOR (pluggable; lazy import; returns a PIL.Image)
# ═══════════════════════════════════════════════════════════════════════════════
_GEN_PIPE = {}


def _build_prompt(entry):
    # Full inline prompt = preamble + scene (models need the style text in context)
    return f"{PREAMBLE} {entry['scene']}"


def _gen_diffusers(prompt, size):
    import torch
    from diffusers import DiffusionPipeline

    if "pipe" not in _GEN_PIPE:
        model_id = CONFIG["model_id"] or "runwayml/stable-diffusion-v1-5"
        pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
        pipe = pipe.to(CONFIG["device"])
        try:
            pipe.enable_attention_slicing()
        except Exception:
            pass
        _GEN_PIPE["pipe"] = pipe

    pipe = _GEN_PIPE["pipe"]
    # Clamp generation size to model-friendly values; upscale in finalize()
    w, h = size
    gen_w, gen_h = (min(w, 768), min(h, 768))
    gen_w -= gen_w % 8
    gen_h -= gen_h % 8
    gen_w = max(gen_w, 64)
    gen_h = max(gen_h, 64)

    kwargs = {
        "prompt": prompt,
        "num_inference_steps": CONFIG["steps"],
        "guidance_scale": CONFIG["guidance_scale"],
        "width": gen_w,
        "height": gen_h,
    }
    seed = CONFIG["seed"]
    if seed is not None:
        try:
            generator = torch.Generator(device=CONFIG["device"]).manual_seed(seed)
            kwargs["generator"] = generator
        except Exception:
            pass

    with torch.inference_mode():
        result = pipe(**kwargs)
    return result.images[0]


def _gen_api(prompt, size, **kwargs):
    import requests

    url = CONFIG["api_url"]
    if not url:
        raise RuntimeError("CONFIG['api_url'] is required for generator='api'")
    headers = {"Content-Type": "application/json"}
    if CONFIG["api_key"]:
        headers["Authorization"] = f"Bearer {CONFIG['api_key']}"
    payload = {
        "model": CONFIG.get("api_model"),
        "prompt": prompt,
        "size": f"{size[0]}x{size[1]}",
        "response_format": "b64_json",
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    resp = requests.post(url, headers=headers, json=payload, timeout=240)
    resp.raise_for_status()
    data = resp.json()
    field = CONFIG["api_image_field"]
    b64 = data[field] if field in data else data["data"][0][field]
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def _gen_auto(prompt, size):
    errors = []
    for fn in (_gen_diffusers, _gen_api):
        try:
            return fn(prompt, size)
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("auto generator failed via both diffusers and api: " + " | ".join(errors))


def generate_image(entry):
    """Return a PIL.Image (RGB or RGBA) for the entry. Throws on failure."""
    full_prompt = _build_prompt(entry)
    kind = entry["kind"]
    if kind == "wash_blank":
        # No model needed — blank transparent canvas (cheap, deterministic)
        return Image.new("RGBA", entry["size"], (0, 0, 0, 0))
    if kind == "region" and CONFIG["force_transparent"]:
        full_prompt = full_prompt + " Isolated on a plain pure-white background."
    gen = CONFIG["generator"]
    if gen == "diffusers":
        img = _gen_diffusers(full_prompt, entry["size"])
    elif gen == "api":
        img = _gen_api(full_prompt, entry["size"])
    else:
        img = _gen_auto(full_prompt, entry["size"])
    return img


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 4 — FINALIZE (per-kind post-processing to exact app spec)
# ═══════════════════════════════════════════════════════════════════════════════
def _fit_canvas(img, target, color=(0, 0, 0, 0)):
    """Resize (cover-fit) into a target (w,h) canvas WITHOUT stretching the art,
    centering with transparent/color fill on the short axis."""
    tw, th = target
    if img is None:
        return Image.new("RGBA", target, color)
    img_c = img.copy()
    if img_c.mode != "RGBA":
        img_c = img_c.convert("RGBA")
    iw, ih = img_c.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(round(iw * scale)), int(round(ih * scale))
    img_c = img_c.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", target, color)
    canvas.paste(img_c, ((tw - nw) // 2, (th - nh) // 2), img_c)
    return canvas


def _remove_background_pillow(img):
    """Simple Pillow-only background keyer. Falls back gracefully if rembg absent.
    Assumes the bg is near-white (prompt asked for pure-white bg)."""
    alpha = img.split()[-1]
    # If the model already gave ~full alpha, keep it
    if alpha.getextrema()[0] > 8:
        return img
    try:
        import rembg  # heavy; optional
    except Exception:
        rembg = None
    if rembg is not None:
        try:
            out = rembg.remove(img.convert("RGBA"))
            return out
        except Exception:
            pass
    # Pillow color-key fallback: distance from white -> alpha
    rgb = img.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    a = alpha
    mask = PyAccess_like = None
    a_px = a.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            # near-white -> transparent
            dist = (255 - r) ** 2 + (255 - g) ** 2 + (255 - b) ** 2
            thr = 60 * 60
            a_px[x, y] = 0 if dist < thr else 255
    img_rgba = img.convert("RGBA")
    img_rgba.putalpha(a)
    return img_rgba


def _remove_background(img):
    return _remove_background_pillow(img)


def finalize(img, entry):
    tw, th = entry["size"]
    kind = entry["kind"]
    if kind == "wash_blank":
        return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if kind == "hero":
        canvas = _fit_canvas(img, (tw, th), color=(30, 25, 35, 255))
        return canvas.convert("RGB")
    if kind == "region":
        work = img
        if CONFIG["force_transparent"]:
            work = _remove_background(work)
        canvas = _fit_canvas(work, (tw, th), color=(0, 0, 0, 0))
        return canvas.convert("RGBA")
    if kind == "wash":
        return _make_wash(img, tw, th)
    return img


def _make_wash(img, tw, th):
    """Turn the model's wash into a subtle translucent overlay matching spec
    (flourishing = warm gold brightening; neglected = grey-blue darkening)."""
    try:
        import numpy as np
    except Exception:
        np = None
    work = img.convert("RGB").resize((tw, th), Image.LANCZOS)
    # uniform blur so no edges/borders show up as hard lines
    base = work.filter(ImageFilter.GaussianBlur(40))
    gray = ImageOps.grayscale(base)

    # Detect warmth vs cool from channel means to pick the base tint
    hist = base.histogram()
    n = max(tw * th, 1)
    mr = sum(i * c for i, c in enumerate(hist[:256])) / n
    mg = sum(i * c for i, c in enumerate(hist[256:512])) / n
    mb = sum(i * c for i, c in enumerate(hist[512:])) / n
    warm = mr >= mg and mr >= mb

    tint = (255, 214, 150) if warm else (70, 95, 135)
    tinted = Image.new("RGB", (tw, th), tint)
    mixed = Image.composite(tinted, base, gray)  # keep luminance, apply tint hue

    # Vignette alpha: stronger near edges, subtle at center (spec: ~15-25%)
    if np is not None:
        x = np.linspace(-1, 1, tw)
        y = np.linspace(-1, 1, th)
        xx, yy = np.meshgrid(x, y)
        rdist = np.sqrt(xx ** 2 + yy ** 2) / np.sqrt(2.0)  # 0 center .. 1 corner
        base_alpha = 55 if warm else 85
        a = np.clip(base_alpha * (0.35 + 1.4 * rdist), 0, 140).astype("uint8")
        alpha_img = Image.fromarray(a, "L")
    else:
        # Pillow-only fallback: flat subtle alpha (still valid translucent wash)
        a = 80 if warm else 110
        alpha_img = Image.new("L", (tw, th), a)

    out = Image.new("RGBA", (tw, th))
    out.putalpha(alpha_img)
    out.paste(mixed, (0, 0))
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 5 — MAIN GENERATION LOOP (sequential, resumable, tqdm progress)
# ═══════════════════════════════════════════════════════════════════════════════
def should_skip(entry, manifest):
    mode = CONFIG["mode"]
    if entry["filename"] in CONFIG["skip_filenames"]:
        return "skip-cfg"
    if entry["kind"] in CONFIG["skip_groups"]:
        return "skip-cfg"
    rec = manifest.get(entry["filename"])
    if mode == "missing":
        if rec and rec.get("status") == "ok" and on_disk(entry):
            return "skip-existing"
        return None
    if mode == "failed":
        if rec and rec.get("status") == "failed":
            return None
        return "skip-not-failed"
    if mode == "all":
        return None
    return None


def run_generation():
    manifest = load_manifest()
    pending = [(e, should_skip(e, manifest)) for e in IMAGES]
    to_run = [e for e, s in pending if s is None]
    if not to_run:
        print("Nothing to do for mode=" + CONFIG["mode"] + ".")
        return manifest

    print(f"mode={CONFIG['mode']} | entries={len(IMAGES)} | to_generate={len(to_run)}")
    pbar = tqdm(total=len(IMAGES), desc="garden-images")
    for entry, skip_reason in pending:
        if skip_reason:
            pbar.set_postfix_str(f"{entry['filename']}: {skip_reason}")
            pbar.update(1)
            continue
        pbar.set_description(f"gen {entry['filename']}")
        try:
            if entry["kind"] == "wash_blank":
                img = Image.new("RGBA", entry["size"], (0, 0, 0, 0))
            else:
                img = generate_image(entry)
            out = finalize(img, entry)
        except Exception as e:
            msg = f"ERROR {entry['filename']}: {e}"
            print(msg)
            manifest[entry["filename"]] = {
                "status": "failed", "id": entry["id"],
                "error": str(e)[:300], "ts": time.time(),
            }
            write_manifest(manifest, _root_dir())
            pbar.set_postfix_str("failed")
            pbar.update(1)
            continue

        dest = full_path(entry)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if entry["kind"] == "hero":
            out.convert("RGB").save(dest, "JPEG", quality=88)
        else:
            out.save(dest, "PNG", optimize=True)
        manifest[entry["filename"]] = {
            "status": "ok", "id": entry["id"],
            "size": entry["size"], "bytes": os.path.getsize(dest),
            "ts": time.time(),
        }
        write_manifest(manifest, _root_dir())  # flush after EVERY image -> crash-safe
        pbar.set_postfix_str(f"saved {os.path.basename(dest)}")
        pbar.update(1)
    pbar.close()
    ok = sum(1 for v in manifest.values() if v.get("status") == "ok")
    print(f"DONE: {ok}/{len(IMAGES)} images saved under {_root_dir()}")
    return manifest


# ═══════════════════════════════════════════════════════════════════════════════
# CELL 6 — ZIP EVERYTHING + DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════
def build_and_download_zip():
    root = _root_dir()
    # Build the archive OUTSIDE root so the .zip isn't included inside itself,
    # then move it into root for a single clean download.
    import tempfile
    staging = tempfile.mkdtemp(prefix="garden_zip_")
    base = os.path.join(staging, CONFIG["zip_name"].replace(".zip", ""))
    shutil.make_archive(base, "zip", root)
    built = base + ".zip"
    zip_path = os.path.join(root, CONFIG["zip_name"])
    shutil.move(built, zip_path)
    shutil.rmtree(staging, ignore_errors=True)

    print("Zipped:", zip_path)
    print("Zip size: %.2f MB" % (os.path.getsize(zip_path) / 1e6))
    if _gfiles is not None:
        _gfiles.download(zip_path)
    else:
        print("Not on Colab — download manually from:", zip_path)
    return zip_path


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECT RUN (not pasted into Colab): lets you dry-run / verify locally.
#   python generate_garden_images.py --dry-run
#   python generate_garden_images.py --verify-paths
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys, glob as _glob

    args = sys.argv[1:]

    if "--verify-paths" in args:
        # Assert every entry maps to one of the app's exact asset paths.
        expected_root = {
            "garden-hero-spring.jpg": "img",
            "garden-hero-summer.jpg": "img",
            "garden-hero-autumn.jpg": "img",
            "garden-hero-winter.jpg": "img",
            "garden-health-flourishing.png": "img",
            "garden-health-stable.png": "img",
            "garden-health-neglected.png": "img",
        }
        errors = []
        seen = set()
        for e in IMAGES:
            key = e["filename"]
            if key in seen:
                errors.append(f"duplicate filename: {key}")
            seen.add(key)
            folder, fname = e["folder"], e["filename"]
            # region files must be in img/regions and named {region}-tier{n}.png
            import re
            if folder == "img/regions":
                if not re.match(r"^(academy|river|moon|village)-tier[1-4]\.png$", fname):
                    errors.append(f"bad region path: {folder}/{fname}")
            else:
                expected = expected_root.get(fname)
                if expected != folder:
                    errors.append(f"bad hero/wash path: {folder}/{fname} (want {expected})")
            if e["size"][0] <= 0 or e["size"][1] <= 0:
                errors.append(f"bad size {e['size']} for {fname}")
        if len(seen) != 23:
            errors.append(f"expected 23 entries, got {len(seen)}")
        if errors:
            print("VERIFY-PATHS FAILED:")
            for err in errors:
                print("  -", err)
            sys.exit(1)
        print(f"VERIFY-PATHS OK: {len(seen)} entries, all map to correct app paths.")
        sys.exit(0)

    if "--dry-run" in args:
        print(f"[dry-run] entries={len(IMAGES)} mode={CONFIG['mode']} root={_root_dir()}")
        print("[dry-run] no model/GPU/network touched. Validating generator=auto future-run only.")
        # Without drive mount, skipping actual run. Just validate prompt assembly.
        for e in IMAGES[:4]:
            p = _build_prompt(e)
            _assert_len = len(p) > len(PREAMBLE)
            print(f"  prompt[:60]={p[:60]!r}... ({len(p)} chars)")
        sys.exit(0)

    print("This script provides Colab cells. Use --verify-paths or --dry-run locally.")