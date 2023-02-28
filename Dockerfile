# 
FROM python:3.10-slim


RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    sox \
    libsox-fmt-all \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
# 
WORKDIR /code

# 
COPY ./app/requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app

# 
CMD ["python", "app/main.py"]