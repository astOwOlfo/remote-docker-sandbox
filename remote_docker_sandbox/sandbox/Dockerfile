FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    sudo \
    python3-full \
    python3-pip \
    python-is-python3 \
    python3-pytest

WORKDIR /app/

CMD ["/bin/bash"]
