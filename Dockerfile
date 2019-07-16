FROM gitpod/workspace-full:latest

# Install postgres
USER root
RUN apt-get update && apt-get install -y \
        python3-jinja2 \
        texlive-full \
    && apt-get clean && rm -rf /var/cache/apt/* && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
