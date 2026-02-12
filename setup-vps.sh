#!/bin/bash
# Soundmaze VPS Setup Script
# Run this on a fresh Ubuntu 24.04 VPS as root
# Usage: ssh root@YOUR_VPS_IP 'bash -s' < setup-vps.sh

set -e

echo "=== Soundmaze VPS Setup ==="

# 1. Update system
echo "--- Updating system packages ---"
apt update && apt upgrade -y

# 2. Create deploy user (don't run everything as root)
echo "--- Creating deploy user ---"
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy
fi

# 3. Set up SSH for deploy user (copy root's authorized keys)
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# 4. Basic firewall
echo "--- Setting up firewall ---"
apt install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# 5. Install Docker
echo "--- Installing Docker ---"
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add deploy user to docker group
usermod -aG docker deploy

# 6. Install git
apt install -y git

# 7. Harden SSH (disable root login and password auth)
echo "--- Hardening SSH ---"
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. SSH in as deploy user: ssh deploy@$(curl -s ifconfig.me)"
echo "  2. Clone your repo and deploy (see DEPLOYMENT.md)"
echo ""
echo "IMPORTANT: root SSH is now disabled. Use 'deploy' user from now on."
