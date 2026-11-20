FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*
