# Dockerfile for SSH/Reverse Shell test container
FROM ubuntu:22.04

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_USER=testuser
ENV SSH_PASS=testpass

# Install required packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    netcat-traditional \
    curl \
    wget \
    python3 \
    python3-pip \
    bash \
    coreutils \
    procps \
    net-tools \
    iproute2 \
    vim \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# SSH configuration
RUN mkdir /var/run/sshd
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config
RUN sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

# Create test user
RUN useradd -m -s /bin/bash $SSH_USER
RUN echo "$SSH_USER:$SSH_PASS" | chpasswd
RUN usermod -aG sudo $SSH_USER

# Create root user with password
RUN echo "root:rootpass" | chpasswd

# Create test directories and files
RUN mkdir -p /tmp/test_files
RUN mkdir -p /home/$SSH_USER/test_data
RUN echo "Test file content for SSH operations" > /tmp/test_files/sample.txt
RUN echo "Large test file content" > /tmp/test_files/large.txt
RUN chown -R $SSH_USER:$SSH_USER /home/$SSH_USER/test_data

# Startup script
COPY start_services.sh /start_services.sh
RUN chmod +x /start_services.sh

# Exposed ports
EXPOSE 22 4444 4445 8080

# Startup command
CMD ["/start_services.sh"]
