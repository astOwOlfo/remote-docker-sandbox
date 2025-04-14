FROM ubuntu:latest

# Make sure we're running commands as root during build
USER root

# Install sudo and necessary packages including Python
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    sudo \
    python3-full \
    python3-pip \
    python-is-python3 \
    python3-pytest && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a regular user
RUN useradd -m docker-user && \
    echo "docker-user:password" | chpasswd

# Create a custom sudoers file that only allows apt and apt-get commands
RUN echo 'Cmnd_Alias APT_COMMANDS = /usr/bin/apt, /usr/bin/apt-get' > /etc/sudoers.d/apt-only && \
    echo 'docker-user ALL=(ALL) APT_COMMANDS' >> /etc/sudoers.d/apt-only && \
    chmod 0440 /etc/sudoers.d/apt-only

# Switch to the regular user
USER docker-user
WORKDIR /home/docker-user

# Default command
CMD ["/bin/bash"]
