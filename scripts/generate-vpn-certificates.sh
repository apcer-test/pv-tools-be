#!/bin/bash

# AWS Client VPN Certificate Generation Script
# This script generates the necessary certificates for AWS Client VPN

set -e

# Configuration
PROJECT_NAME=${1:-"apcer"}
ENV=${2:-"dev"}
DOMAIN=${3:-"vpn.webelight.co.in"}
CERT_DIR="./vpn-certificates"

echo "Generating AWS Client VPN Certificates..."
echo "Project: $PROJECT_NAME"
echo "Environment: $ENV"
echo "Domain: $DOMAIN"

# Create certificates directory
mkdir -p "$CERT_DIR"

# Generate CA private key
echo "Generating CA private key..."
openssl genrsa -out "$CERT_DIR/ca.key" 2048

# Generate CA certificate
echo "Generating CA certificate..."
openssl req -new -x509 -key "$CERT_DIR/ca.key" -sha256 -days 3650 -out "$CERT_DIR/ca.crt" \
  -subj "/C=IN/ST=Karnataka/L=Bangalore/O=$PROJECT_NAME/CN=$PROJECT_NAME-$ENV-CA"

# Generate server private key
echo "Generating server private key..."
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate server certificate signing request
echo "Generating server certificate signing request..."
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
  -subj "/C=IN/ST=Karnataka/L=Bangalore/O=$PROJECT_NAME/CN=server.$DOMAIN"

# Generate server certificate
echo "Generating server certificate..."
openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" \
  -CAcreateserial -out "$CERT_DIR/server.crt" -days 3650 -sha256

# Generate client private key
echo "Generating client private key..."
openssl genrsa -out "$CERT_DIR/client.key" 2048

# Generate client certificate signing request
echo "Generating client certificate signing request..."
openssl req -new -key "$CERT_DIR/client.key" -out "$CERT_DIR/client.csr" \
  -subj "/C=IN/ST=Karnataka/L=Bangalore/O=$PROJECT_NAME/CN=client.$DOMAIN"

# Generate client certificate
echo "Generating client certificate..."
openssl x509 -req -in "$CERT_DIR/client.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" \
  -CAcreateserial -out "$CERT_DIR/client.crt" -days 3650 -sha256

# Create client certificate bundle
echo "Creating client certificate bundle..."
cat "$CERT_DIR/client.crt" "$CERT_DIR/ca.crt" > "$CERT_DIR/client.crt.bundle"

# Set proper permissions
chmod 600 "$CERT_DIR"/*.key
chmod 644 "$CERT_DIR"/*.crt

echo "Certificate generation complete!"
echo ""
echo "Certificates created in: $CERT_DIR"
echo ""
echo "Next steps:"
echo "1. Upload server.crt and ca.crt to AWS ACM (us-east-1 region)"
echo "2. Download client.crt.bundle and client.key for your machine"
echo "3. Install AWS VPN Client on your machine"
echo "4. Configure the VPN connection"
echo ""
echo "Certificate files:"
echo "  - ca.crt: Certificate Authority (upload to ACM)"
echo "  - server.crt: Server certificate (upload to ACM)"
echo "  - client.crt.bundle: Client certificate bundle (install on machine)"
echo "  - client.key: Client private key (install on machine)" 