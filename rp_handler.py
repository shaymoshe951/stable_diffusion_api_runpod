# rp_handler.py
import os, time, json, base64, subprocess, requests
import sys

import runpod

WEBUI_PORT = int(os.getenv("WEBUI_PORT", "3000"))
WEBUI_URL  = f"http://127.0.0.1:{WEBUI_PORT}"
WEBUI_ARGS = os.getenv("WEBUI_ARGS", "--api --nowebui --port=3000")

WEBUI_CMD = f"python3 launch.py {WEBUI_ARGS}"

def start_webui():
    # Start AUTOMATIC1111 headless (detached)
    subprocess.Popen(
        WEBUI_CMD,
        shell=True,
        cwd="/app",
        # stdout=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # Wait until API is up
    for _ in range(120):  # up to ~120s
        try:
            r = requests.get(f"{WEBUI_URL}/sdapi/v1/progress", timeout=2)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("AUTOMATIC1111 API did not become ready.")

def ensure_ready():
    try:
        r = requests.get(f"{WEBUI_URL}/sdapi/v1/sd-models", timeout=5)
        r.raise_for_status()
    except Exception:
        start_webui()

def call_api(path, payload):
    url = f"{WEBUI_URL}{path}"
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

# Cold start boot
ensure_ready()

# ---- Handlers -------------------------------------------------
def handle_txt2img(job):
    """
    job['input'] should include fields accepted by /sdapi/v1/txt2img, e.g.:
    {
      "prompt": "a photorealistic cat",
      "negative_prompt": "",
      "width": 512, "height": 512, "steps": 20, "cfg_scale": 7,
      "sampler_name": "DPM++ 2M", "seed": 12345
    }
    """
    payload = job["input"]
    result = call_api("/sdapi/v1/txt2img", payload)
    # return first image
    img_b64 = result["images"][0]
    return {"image_b64": img_b64}

def handle_img2img(job):
    """
    job['input'] example:
    {
      "prompt": "make it cinematic",
      "init_images": ["<base64>"],  # list of b64 JPG/PNG
      "mask": "<optional b64 mask>",
      "denoising_strength": 0.6,
      "width": 512, "height": 512, "steps": 20, "cfg_scale": 7
    }
    """
    payload = job["input"]
    result = call_api("/sdapi/v1/img2img", payload)
    img_b64 = result["images"][0]
    return {"image_b64": img_b64}

def handle_ping_is_alive(job):
    try:
        r = requests.get(f"{WEBUI_URL}/sdapi/v1/sd-models", timeout=5)
        return {"alive": bool(r.ok)}
    except Exception as e:
        return {"alive": False, "error": str(e)}

ROUTES = {
    "txt2img": handle_txt2img,
    "img2img": handle_img2img,
    "ping_is_alive": handle_ping_is_alive,
}

def handler(job):
    """
    job = {
      "input": {...},               # payload for A1111 endpoint
      "endpoint": "txt2img"|"img2img"  # which route to call
    }
    """
    ensure_ready()
    endpoint = job['input'].get("endpoint", "img2img")
    if 'endpoint' in job['input']:
        del job['input']['endpoint']
    print(f"payload:", job)

    if endpoint not in ROUTES:
        return {"error": f"Unknown endpoint '{endpoint}'."}
    try:
        return ROUTES[endpoint](job)
    except Exception as e:
        return {"error": str(e)}
print(r"Starting RunPod serverless...9/7/2025_20:35")
runpod.serverless.start({"handler": handler})
