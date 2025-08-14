# AWS VPN Connection Guide

This guide explains how to connect to the AWS VPN from your local machine.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Certificate Generation](#certificate-generation)
3. [AWS Client VPN Setup](#aws-client-vpn-setup)
4. [Client Machine Setup](#client-machine-setup)
5. [Connection Instructions](#connection-instructions)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before connecting to the VPN, ensure you have:

- AWS Client VPN endpoint created and active
- Client certificates generated and installed
- AWS VPN Client installed on your machine
- Proper network permissions

## Certificate Generation

### Step 1: Generate Certificates

Run the certificate generation script:

```bash
# Navigate to the project root
cd /path/to/apcer-infra

# Run the certificate generation script
./scripts/generate-vpn-certificates.sh apcer dev vpn.webelight.co.in
```

This will create certificates in the `vpn-certificates/` directory.

### Step 2: Upload Certificates to AWS

1. **Go to AWS Certificate Manager (ACM)**
   - Navigate to the **us-east-1** region
   - Click "Import a certificate"

2. **Import Server Certificate**
   - Certificate body: Copy content from `vpn-certificates/server.crt`
   - Certificate private key: Copy content from `vpn-certificates/server.key`
   - Certificate chain: Copy content from `vpn-certificates/ca.crt`

3. **Import CA Certificate**
   - Certificate body: Copy content from `vpn-certificates/ca.crt`
   - No private key needed for CA certificate

## AWS Client VPN Setup

### Step 1: Enable VPN in Terraform

Update your `terraform.tfvars`:

```hcl
create_aws_vpn = true
aws_vpn = {
  create_client_vpn = true
  client_vpn_cidr_block = "172.31.0.0/16"
  client_vpn_subnet_ids = [
    # Add your private subnet IDs
    "subnet-12345678",
    "subnet-87654321"
  ]
  client_vpn_authorized_networks = [
    "10.10.0.0/16",  # VPC CIDR
    "172.31.0.0/16"  # Client VPN CIDR
  ]
  client_vpn_domain = "vpn.webelight.co.in"
  split_tunnel = true
  enable_connection_logging = false
}
```

### Step 2: Deploy VPN Infrastructure

```bash
terraform plan
terraform apply
```

### Step 3: Get VPN Endpoint Details

After deployment, get the VPN endpoint DNS name:

```bash
terraform output client_vpn_endpoint_dns_name
```

## Client Machine Setup

### Step 1: Install AWS VPN Client

#### **macOS:**
```bash
# Using Homebrew
brew install --cask aws-vpn-client

# Or download from AWS
curl -O https://d20adtppz83p9s.cloudfront.net/OSX/latest/AWS_VPN_Client.pkg
sudo installer -pkg AWS_VPN_Client.pkg -target /
```

#### **Windows:**
1. Download from: https://aws.amazon.com/vpn/client-vpn-download/
2. Run the installer as administrator

#### **Linux (Ubuntu/Debian):**
```bash
# Download and install
wget https://d20adtppz83p9s.cloudfront.net/Linux/latest/AWS_VPN_Client.deb
sudo dpkg -i AWS_VPN_Client.deb
sudo apt-get install -f  # Fix any dependencies
```

### Step 2: Install Client Certificates

#### **macOS/Linux:**
```bash
# Copy certificates to the correct location
sudo cp vpn-certificates/client.crt.bundle /opt/aws-vpn-client/certs/
sudo cp vpn-certificates/client.key /opt/aws-vpn-client/certs/

# Set proper permissions
sudo chmod 600 /opt/aws-vpn-client/certs/client.key
sudo chmod 644 /opt/aws-vpn-client/certs/client.crt.bundle
```

#### **Windows:**
1. Copy certificates to: `C:\ProgramData\AWS VPN Client\certs\`
2. Ensure proper file permissions

## Connection Instructions

### Step 1: Configure VPN Connection

1. **Open AWS VPN Client**

2. **Add a new connection:**
   - Click "Add Connection"
   - Enter connection details:
     - **Name**: `apcer-dev-vpn`
     - **Server endpoint**: `[VPN_ENDPOINT_DNS_NAME]` (from terraform output)
     - **Client certificate**: Browse to `client.crt.bundle`
     - **Client private key**: Browse to `client.key`

3. **Advanced settings:**
   - **Split tunnel**: Enabled (recommended)
   - **DNS servers**: Use AWS DNS (10.0.0.2)

### Step 2: Connect to VPN

1. **Select your connection** from the list
2. **Click "Connect"**
3. **Enter your credentials** if prompted
4. **Wait for connection** to establish

### Step 3: Verify Connection

```bash
# Check your IP address
curl ifconfig.me

# Test connectivity to VPC resources
ping 10.10.0.10  # Replace with your VPC IP

# Check routing table
netstat -rn | grep 172.31
```

## Connection Details

### **VPN Endpoint Information:**
- **DNS Name**: `[VPN_ENDPOINT_DNS_NAME]`
- **Protocol**: OpenVPN
- **Port**: 443 (HTTPS)
- **Authentication**: Certificate-based

### **Network Configuration:**
- **Client CIDR**: `172.31.0.0/16`
- **VPC CIDR**: `10.10.0.0/16`
- **Split Tunnel**: Enabled (only VPC traffic goes through VPN)

### **Accessible Resources:**
- Private subnets in VPC
- RDS databases
- ElastiCache Redis
- ECS services (internal)
- S3 buckets (if configured)

## Troubleshooting

### **Common Issues:**

#### **1. Certificate Errors**
```
Error: Certificate validation failed
```
**Solution:**
- Verify certificate paths are correct
- Check certificate permissions (600 for key, 644 for cert)
- Ensure certificates are in the correct format

#### **2. Connection Timeout**
```
Error: Connection timeout
```
**Solution:**
- Check firewall settings (port 443)
- Verify VPN endpoint is active
- Check network connectivity

#### **3. DNS Resolution Issues**
```
Error: Cannot resolve hostnames
```
**Solution:**
- Use AWS DNS servers (10.0.0.2, 10.0.0.3)
- Check split tunnel configuration
- Verify VPC DNS settings

#### **4. Authentication Failed**
```
Error: Authentication failed
```
**Solution:**
- Verify client certificate is valid
- Check server certificate in ACM
- Ensure CA certificate is imported

### **Debug Commands:**

```bash
# Check VPN client status
aws-vpn-client status

# View connection logs
tail -f /var/log/aws-vpn-client.log

# Test endpoint connectivity
telnet [VPN_ENDPOINT_DNS_NAME] 443

# Check certificate validity
openssl x509 -in client.crt.bundle -text -noout
```

### **AWS Console Verification:**

1. **Go to AWS Client VPN**
2. **Check endpoint status** - should be "Available"
3. **View active connections** - your connection should appear
4. **Check CloudWatch logs** - for connection issues

## Security Best Practices

### **Certificate Management:**
- Store certificates securely
- Use strong private keys (2048-bit minimum)
- Rotate certificates regularly
- Limit certificate access

### **Network Security:**
- Use split tunnel (only VPC traffic)
- Restrict authorized networks
- Monitor connection logs
- Use least privilege access

### **Client Security:**
- Keep VPN client updated
- Use strong authentication
- Disconnect when not in use
- Monitor for suspicious activity

## Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Review AWS Client VPN documentation**
3. **Check CloudWatch logs for errors**
4. **Contact your DevOps team**

---

**Note**: This guide assumes you have the necessary AWS permissions and the VPN infrastructure is properly configured. Always follow your organization's security policies when connecting to corporate networks. 