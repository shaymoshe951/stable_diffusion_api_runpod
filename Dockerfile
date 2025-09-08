# =========================================================
# Base image: CUDA 12.1.1 + cuDNN 8 + Ubuntu 22.04
# =========================================================
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# ---------- Environment ----------
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ---------- System dependencies ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget curl python3 python3-venv python3-pip python3-dev \
    build-essential libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ---------- Copy AUTOMATIC1111 project ----------
WORKDIR /app
# RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git .
# (Optional) checkout stable branch
# RUN git checkout master
COPY . .

# ---------- Python venv ----------
RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# ---------- Install requirements ----------
RUN pip install --upgrade pip wheel
#RUN pip install -r requirements_versions.txt
RUN python3 install_env.py --skip-torch-cuda-test
RUN pip install runpod requests


# (Optional) install xformers for faster attention
RUN pip install xformers==0.0.27.post2 --extra-index-url https://download.pytorch.org/whl/cu121

# ---------- Expose WebUI ----------
EXPOSE 7860

# ---------- Launch ----------
CMD ["python3", "rp_handler.py"]
#CMD ["python3", "launch.py", "--listen", "--xformers","--nowebui"]
