# AWS VPN Quick Reference

## 🚀 Quick Setup

### 1. Enable VPN in Terraform
```hcl
# In terraform.tfvars
create_aws_vpn = true
aws_vpn = {
  create_client_vpn = true
  client_vpn_subnet_ids = ["subnet-12345678", "subnet-87654321"]
}
```

### 2. Deploy VPN
```bash
terraform apply
```

### 3. Generate Certificates
```bash
./scripts/generate-vpn-certificates.sh apcer dev vpn.webelight.co.in
```

### 4. Setup Client Connection
```bash
./scripts/setup-vpn-connection.sh apcer dev
```

## 🔗 Connection Details

| Item | Value |
|------|-------|
| **Protocol** | OpenVPN |
| **Port** | 443 (HTTPS) |
| **Authentication** | Certificate-based |
| **Split Tunnel** | Enabled (recommended) |
| **Client CIDR** | 172.31.0.0/16 |
| **VPC CIDR** | 10.10.0.0/16 |

## 📱 Client Installation

### macOS
```bash
brew install --cask aws-vpn-client
```

### Windows
Download from: https://aws.amazon.com/vpn/client-vpn-download/

### Linux
```bash
wget https://d20adtppz83p9s.cloudfront.net/Linux/latest/AWS_VPN_Client.deb
sudo dpkg -i AWS_VPN_Client.deb
```

## 🔧 Connection Configuration

1. **Open AWS VPN Client**
2. **Add Connection:**
   - Name: `apcer-dev-vpn`
   - Server: `[VPN_ENDPOINT_DNS_NAME]`
   - Client Cert: `/opt/aws-vpn-client/certs/client.crt.bundle`
   - Client Key: `/opt/aws-vpn-client/certs/client.key`
3. **Enable Split Tunnel**
4. **Connect**

## ✅ Verification Commands

```bash
# Check IP
curl ifconfig.me

# Test VPC connectivity
ping 10.10.0.10

# Check routing
netstat -rn | grep 172.31

# VPN client status
aws-vpn-client status
```

## 🚨 Troubleshooting

### Certificate Issues
```bash
# Check certificate validity
openssl x509 -in client.crt.bundle -text -noout

# Verify permissions
ls -la /opt/aws-vpn-client/certs/
```

### Connection Issues
```bash
# Test endpoint
telnet [VPN_ENDPOINT] 443

# Check logs
tail -f /var/log/aws-vpn-client.log
```

### DNS Issues
- Use AWS DNS: 10.0.0.2, 10.0.0.3
- Enable split tunnel
- Check VPC DNS settings

## 📋 Accessible Resources

- ✅ Private subnets (10.10.x.x)
- ✅ RDS databases
- ✅ ElastiCache Redis
- ✅ ECS services (internal)
- ✅ S3 buckets (if configured)

## 🔒 Security Notes

- Store certificates securely
- Use strong private keys
- Rotate certificates regularly
- Monitor connection logs
- Disconnect when not in use

## 📞 Support

- Check: `docs/VPN_CONNECTION_GUIDE.md`
- AWS Console: Client VPN service
- CloudWatch logs for errors
- Contact DevOps team

---

**Quick Command**: `./scripts/setup-vpn-connection.sh apcer dev` 