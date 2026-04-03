#!/bin/bash
# Generates self-signed CA + server + client certs for local MQTT TLS
# Run once on first install. Output goes to services/mqtt/certs/

CERTS_DIR="$(dirname $0)/certs"
mkdir -p $CERTS_DIR

# CA
openssl genrsa -out $CERTS_DIR/ca.key 2048
openssl req -new -x509 -days 3650 -key $CERTS_DIR/ca.key \
  -out $CERTS_DIR/ca.crt \
  -subj "/CN=NestShift-CA/O=NestShift/C=GB"

# Server cert
openssl genrsa -out $CERTS_DIR/server.key 2048
openssl req -new -key $CERTS_DIR/server.key \
  -out $CERTS_DIR/server.csr \
  -subj "/CN=nestshift.local/O=NestShift/C=GB"
openssl x509 -req -days 3650 \
  -in $CERTS_DIR/server.csr \
  -CA $CERTS_DIR/ca.crt \
  -CAkey $CERTS_DIR/ca.key \
  -CAcreateserial \
  -out $CERTS_DIR/server.crt

# Client cert (for agents)
openssl genrsa -out $CERTS_DIR/client.key 2048
openssl req -new -key $CERTS_DIR/client.key \
  -out $CERTS_DIR/client.csr \
  -subj "/CN=nestshift-agent/O=NestShift/C=GB"
openssl x509 -req -days 3650 \
  -in $CERTS_DIR/client.csr \
  -CA $CERTS_DIR/ca.crt \
  -CAkey $CERTS_DIR/ca.key \
  -CAcreateserial \
  -out $CERTS_DIR/client.crt

echo "Certs generated in $CERTS_DIR"
echo "Add ca.crt to all MQTT clients"