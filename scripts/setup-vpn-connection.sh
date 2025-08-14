#!/bin/bash

# AWS VPN Connection Setup Script
# This script helps set up VPN connection on your local machine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME=${1:-"apcer"}
ENV=${2:-"dev"}
CERT_DIR="./vpn-certificates"

echo -e "${BLUE} AWS VPN Connection Setup${NC}"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENV"
echo ""

# Check if certificates exist
if [ ! -d "$CERT_DIR" ]; then
    echo -e "${YELLOW}  Certificates not found. Generating them first...${NC}"
    ./scripts/generate-vpn-certificates.sh "$PROJECT_NAME" "$ENV"
    echo ""
fi

# Check if AWS VPN Client is installed
check_vpn_client() {
    case "$(uname -s)" in
        Darwin*)    # macOS
            if [ -d "/Applications/AWS VPN Client.app" ]; then
                return 0
            fi
            ;;
        Linux*)     # Linux
            if command -v aws-vpn-client &> /dev/null; then
                return 0
            fi
            ;;
        MINGW*|CYGWIN*|MSYS*)  # Windows
            if [ -d "C:/Program Files/AWS VPN Client" ]; then
                return 0
            fi
            ;;
    esac
    return 1
}

if ! check_vpn_client; then
    echo -e "${YELLOW}  AWS VPN Client not found.${NC}"
    echo ""
    echo "Please install AWS VPN Client:"
    echo ""
    case "$(uname -s)" in
        Darwin*)    # macOS
            echo "macOS:"
            echo "  brew install --cask aws-vpn-client"
            echo "  or download from: https://aws.amazon.com/vpn/client-vpn-download/"
            ;;
        Linux*)     # Linux
            echo "Linux:"
            echo "  wget https://d20adtppz83p9s.cloudfront.net/Linux/latest/AWS_VPN_Client.deb"
            echo "  sudo dpkg -i AWS_VPN_Client.deb"
            ;;
        MINGW*|CYGWIN*|MSYS*)  # Windows
            echo "Windows:"
            echo "  Download from: https://aws.amazon.com/vpn/client-vpn-download/"
            ;;
    esac
    echo ""
    read -p "Press Enter after installing AWS VPN Client..."
fi

# Get VPN endpoint DNS name from terraform output
echo -e "${BLUE} Getting VPN endpoint details...${NC}"
cd main

if ! command -v terraform &> /dev/null; then
    echo -e "${RED} Terraform not found. Please install Terraform first.${NC}"
    exit 1
fi

VPN_ENDPOINT=$(terraform output -raw client_vpn_endpoint_dns_name 2>/dev/null || echo "")

if [ -z "$VPN_ENDPOINT" ]; then
    echo -e "${YELLOW}  VPN endpoint not found in terraform output.${NC}"
    echo "Please ensure VPN is deployed and enabled in terraform.tfvars"
    echo ""
    echo "To enable VPN, set in terraform.tfvars:"
    echo "  create_aws_vpn = true"
    echo "  aws_vpn.create_client_vpn = true"
    echo ""
    echo "Then run: terraform apply"
    exit 1
fi

echo -e "${GREEN} VPN Endpoint: $VPN_ENDPOINT${NC}"
echo ""

# Copy certificates to appropriate location
echo -e "${BLUE} Installing certificates...${NC}"

case "$(uname -s)" in
    Darwin*)    # macOS
        CERT_PATH="/opt/aws-vpn-client/certs"
        sudo mkdir -p "$CERT_PATH"
        sudo cp "../$CERT_DIR/client.crt.bundle" "$CERT_PATH/"
        sudo cp "../$CERT_DIR/client.key" "$CERT_PATH/"
        sudo chmod 600 "$CERT_PATH/client.key"
        sudo chmod 644 "$CERT_PATH/client.crt.bundle"
        echo -e "${GREEN} Certificates installed to: $CERT_PATH${NC}"
        ;;
    Linux*)     # Linux
        CERT_PATH="/opt/aws-vpn-client/certs"
        sudo mkdir -p "$CERT_PATH"
        sudo cp "../$CERT_DIR/client.crt.bundle" "$CERT_PATH/"
        sudo cp "../$CERT_DIR/client.key" "$CERT_PATH/"
        sudo chmod 600 "$CERT_PATH/client.key"
        sudo chmod 644 "$CERT_PATH/client.crt.bundle"
        echo -e "${GREEN} Certificates installed to: $CERT_PATH${NC}"
        ;;
    MINGW*|CYGWIN*|MSYS*)  # Windows
        CERT_PATH="C:/ProgramData/AWS VPN Client/certs"
        mkdir -p "$CERT_PATH"
        cp "../$CERT_DIR/client.crt.bundle" "$CERT_PATH/"
        cp "../$CERT_DIR/client.key" "$CERT_PATH/"
        echo -e "${GREEN} Certificates installed to: $CERT_PATH${NC}"
        ;;
esac

echo ""
echo -e "${GREEN} VPN setup complete!${NC}"
echo ""
echo -e "${BLUE} Next steps:${NC}"
echo "1. Open AWS VPN Client"
echo "2. Add a new connection with these details:"
echo "   - Name: ${PROJECT_NAME}-${ENV}-vpn"
echo "   - Server endpoint: $VPN_ENDPOINT"
echo "   - Client certificate: $CERT_PATH/client.crt.bundle"
echo "   - Client private key: $CERT_PATH/client.key"
echo "3. Enable split tunnel (recommended)"
echo "4. Connect to the VPN"
echo ""
echo -e "${BLUE} To verify connection:${NC}"
echo "  curl ifconfig.me"
echo "  ping 10.10.0.10  # Replace with your VPC IP"
echo ""
echo -e "${YELLOW} For detailed instructions, see: docs/VPN_CONNECTION_GUIDE.md${NC}" 