#!/bin/bash

# Bastion Host Setup Script
# Simple setup: PostgreSQL client tools + SSH tunnel user for RDS access

set -e

# Log all output
exec > >(tee /var/log/bastion-setup.log) 2>&1

echo "Starting bastion host setup for RDS tunneling..."

# Update system
apt-get update -y
apt-get upgrade -y

# Install PostgreSQL client tools only (for connecting to RDS)
echo "Installing PostgreSQL client tools..."
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
apt-get update -y
apt-get install -y postgresql-client postgresql-client-common

echo "PostgreSQL client tools installation completed"

# Create database tunnel user for SSH tunneling to RDS
echo "Creating database tunnel user..."

# Create the user
useradd -m -s /bin/bash developer

# Create .ssh directory
mkdir -p /home/developer/.ssh
chown developer:developer /home/developer/.ssh
chmod 700 /home/developer/.ssh

# Add developer public key if provided
if [ ! -z "${developer_public_key}" ]; then
    echo "${developer_public_key}" > /home/developer/.ssh/authorized_keys
    chown developer:developer /home/developer/.ssh/authorized_keys
    chmod 600 /home/developer/.ssh/authorized_keys
    echo "Developer public key added for developer"
fi

# Configure SSH for secure tunneling
echo "Configuring SSH for secure tunneling to RDS..."

# Backup original sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Add SSH tunnel configuration for developer
cat >> /etc/ssh/sshd_config << 'EOF'

# Database tunnel user configuration for RDS access
Match User developer
    AllowTcpForwarding yes
    X11Forwarding no
    PermitTunnel yes
    GatewayPorts no
    ForceCommand /bin/false
    AllowAgentForwarding no
    PasswordAuthentication no
    PubkeyAuthentication yes
EOF

# Restart SSH service
systemctl restart sshd

echo "SSH tunnel configuration completed"

echo "=== Bastion Host Setup Completed ==="
echo "PostgreSQL client tools are installed"
echo "Tunnel user 'developer' is configured for RDS access"
echo "Connect to RDS: ssh -i developer.pem -L 5432:RDS_ENDPOINT:5432 developer@BASTION_IP -N"
echo "Then use: psql -h localhost -p 5432 -U your_rds_user -d your_rds_database"

# Create completion marker
touch /var/log/bastion-setup-complete 