# MedTrack Distributed Deployment Guide

This directory contains Docker Compose files for deploying MedTrack across **5 separate machines**.

## Architecture Overview

| Machine | Role | File | Default Ports |
|---------|------|------|---------------|
| Machine 1 | RabbitMQ | `docker-compose.rabbitmq.yml` | 5672, 15672 |
| Machine 2 | Traefik API Gateway | `docker-compose.traefik.yml` | 80, 443, 8090 |
| Machine 3 | Consul Service Discovery | `docker-compose.consul.yml` | 8500, 8600 |
| Machine 4 | Frontend (Next.js) | Manual deployment | 3000 |
| Machine 5 | Backend Services | `docker-compose.services.yml` | 8001-8005, 5432, 6379, 9000 |

## Pre-Deployment Checklist

### 1. Note Down All Machine IPs

| Machine | Example IP | Your IP |
|---------|------------|---------|
| Machine 1 (RabbitMQ) | 192.168.1.101 | _________ |
| Machine 2 (Traefik) | 192.168.1.102 | _________ |
| Machine 3 (Consul) | 192.168.1.103 | _________ |
| Machine 4 (Frontend) | 192.168.1.104 | _________ |
| Machine 5 (Services) | 192.168.1.105 | _________ |

### 2. Ensure Network Connectivity
All machines must be able to reach each other on the specified ports.

## Deployment Steps

### Step 1: Deploy RabbitMQ (Machine 1)

```bash
# Copy docker-compose.rabbitmq.yml to Machine 1
scp docker-compose.rabbitmq.yml user@MACHINE_1_IP:~/

# SSH into Machine 1 and run
ssh user@MACHINE_1_IP
docker-compose -f docker-compose.rabbitmq.yml up -d
```

### Step 2: Deploy Consul (Machine 3)

```bash
# Copy docker-compose.consul.yml to Machine 3
scp docker-compose.consul.yml user@MACHINE_3_IP:~/

# SSH into Machine 3 and run
ssh user@MACHINE_3_IP
docker-compose -f docker-compose.consul.yml up -d
```

### Step 3: Deploy Backend Services (Machine 5)

**Before copying, update the following in `docker-compose.services.yml`:**
- Replace `MACHINE_1_IP` with your RabbitMQ server IP
- Replace `MACHINE_3_IP` with your Consul server IP

```bash
# Copy the services directory to Machine 5
scp -r services/ user@MACHINE_5_IP:~/medtrack/
scp docker-compose.services.yml user@MACHINE_5_IP:~/medtrack/
scp -r infrastructure/ user@MACHINE_5_IP:~/medtrack/

# SSH into Machine 5 and run
ssh user@MACHINE_5_IP
cd ~/medtrack
docker-compose -f docker-compose.services.yml up -d --build
```

### Step 4: Deploy Traefik (Machine 2)

**Before copying, update `traefik/dynamic.yml`:**
- Replace `MACHINE_5_IP` with your backend services IP

```bash
# Copy traefik files to Machine 2
scp docker-compose.traefik.yml user@MACHINE_2_IP:~/
scp -r traefik/ user@MACHINE_2_IP:~/

# SSH into Machine 2 and run
ssh user@MACHINE_2_IP
docker-compose -f docker-compose.traefik.yml up -d
```

### Step 5: Deploy Frontend (Machine 4)

```bash
# Copy frontend directory to Machine 4
scp -r ../front/ user@MACHINE_4_IP:~/medtrack-front/

# SSH into Machine 4
ssh user@MACHINE_4_IP
cd ~/medtrack-front

# Update .env.local with Traefik IP
echo "NEXT_PUBLIC_API_URL=http://MACHINE_2_IP" > .env.local
echo "NEXTAUTH_URL=http://MACHINE_4_IP:3000" >> .env.local
echo "NEXTAUTH_SECRET=your-secret-key-here" >> .env.local

# Install dependencies and run
npm install
npm run build
npm run start
```

## Verification

### Check RabbitMQ (Machine 1)
```bash
curl http://MACHINE_1_IP:15672  # Management UI
```

### Check Consul (Machine 3)
```bash
curl http://MACHINE_3_IP:8500/v1/status/leader
```

### Check Traefik (Machine 2)
```bash
curl http://MACHINE_2_IP:8090/api/overview  # Dashboard
```

### Check Backend Services (Machine 5)
```bash
curl http://MACHINE_5_IP:8001/health  # Auth service
curl http://MACHINE_5_IP:8002/health  # Profile service
```

### Check Frontend (Machine 4)
```bash
curl http://MACHINE_4_IP:3000
```

## Firewall Rules

Ensure the following ports are open:

| Machine | Inbound Ports |
|---------|---------------|
| Machine 1 | 5672, 15672 |
| Machine 2 | 80, 443, 8090 |
| Machine 3 | 8500, 8600/udp |
| Machine 4 | 3000 |
| Machine 5 | 5432, 6379, 9000, 9001, 8001-8005 |

## Troubleshooting

### Services can't connect to RabbitMQ
- Verify Machine 1 IP is correct in `docker-compose.services.yml`
- Check firewall allows port 5672

### Services can't register with Consul
- Verify Machine 3 IP is correct
- Check Consul is running: `docker logs consul`

### Frontend can't reach backend
- Verify Machine 2 (Traefik) IP in frontend `.env.local`
- Check Traefik routes in `traefik/dynamic.yml`
