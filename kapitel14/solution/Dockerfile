# docker build -t butler:ci -f kapitel14/solution/Dockerfile .
# (Kontext: Wurzel des Begleit-Repositorys)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && git config --system --add safe.directory /work
COPY kapitel14/solution/agent-requirements.txt /tmp/req.txt
RUN uv venv /opt/venv \
 && uv pip install --python /opt/venv/bin/python \
    --require-hashes -r /tmp/req.txt
COPY kapitel09/solution/ /opt/butler/
RUN useradd --uid 1000 --create-home agent
ENV PYTHONUTF8=1 PYDANTIC_AI_NO_BANNER=1
USER agent
WORKDIR /work
ENTRYPOINT ["/opt/venv/bin/python", "/opt/butler/cli.py"]
