# Soundmaze — VPS Deployment Guide

## Overview

This guide walks you through deploying Soundmaze on an Aruba Cloud VPS using Docker Compose. By the end you'll have the app running at `https://app.soundmaze.com` (or whatever domain you choose) with automatic HTTPS.

**What's different from the dev docker-compose:**
- Caddy reverse proxy handles HTTPS automatically (free Let's Encrypt certs)
- Gunicorn replaces Flask's dev server
- Secrets come from `.env` file (not hardcoded)
- Dev tools removed (Adminer, Maildev)
- Alpine-based images (smaller, more secure)
- `restart: unless-stopped` on all services

**Cost:** ~€2.79/month (Aruba Cloud VPS Smart S)

---

## Step 1: Get a VPS

### Option A: Aruba Cloud (recommended — same account as your hosting)

1. Go to [arubacloud.com](https://www.arubacloud.com/vps/) and log in with your Aruba account
2. Create a new **VPS Smart S** (1 vCPU, 1 GB RAM, 20 GB SSD) — this is plenty for a PoC
3. Choose **Ubuntu 24.04** as the OS
4. Set a root password (you'll change auth method later)
5. Note the **public IP address** they assign you

### Option B: Hetzner (better performance/value)

1. Go to [hetzner.com/cloud](https://www.hetzner.com/cloud/)
2. Create a **CX22** server (2 vCPU, 4 GB RAM) for €3.79/mo
3. Choose **Ubuntu 24.04**, add your SSH key
4. Note the IP address

---

## Step 2: Set up SSH access

On your Mac, generate an SSH key if you don't have one:

```bash
# Check if you already have one
ls ~/.ssh/id_ed25519.pub

# If not, generate one
ssh-keygen -t ed25519 -C "your-email@example.com"
```

Copy your public key to the VPS:

```bash
ssh-copy-id root@YOUR_VPS_IP
```

Test that you can log in without a password:

```bash
ssh root@YOUR_VPS_IP
```

---

## Step 3: Secure the VPS

Run the setup script on the server:

```bash
# From your Mac
ssh root@YOUR_VPS_IP 'bash -s' < setup-vps.sh
```

This script:
- Updates the system
- Creates a `deploy` user with Docker access
- Sets up a firewall (only SSH, HTTP, HTTPS open)
- Installs Docker and Docker Compose
- Hardens SSH (disables root login and password auth)

**After this, always connect as:**

```bash
ssh deploy@YOUR_VPS_IP
```

---

## Step 4: Deploy the app

SSH into the server as the deploy user:

```bash
ssh deploy@YOUR_VPS_IP
```

Clone your repository:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/InteractiveAudioGame.git soundmaze
cd soundmaze
```

> **If your repo is private**, you'll need to set up a GitHub deploy key or personal access token first.

Create and edit the `.env` file:

```bash
cp .env.template .env
nano .env
```

Fill in real values. Generate a secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Edit the Caddyfile for **initial testing without a domain**:

```bash
nano Caddyfile
```

Set it to:
```
:80 {
    reverse_proxy flask:8000
}
```

Launch everything:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Watch the logs to confirm everything starts:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

**Test it:** Open `http://YOUR_VPS_IP` in your browser.

---

## Step 5: Point your domain

In your **Aruba hosting control panel** (where you manage DNS):

1. Add an **A record**:
   - Name: `app` (creates `app.soundmaze.com`)
   - Value: `YOUR_VPS_IP`
   - TTL: 300

2. Wait for DNS propagation (check at [dnschecker.org](https://dnschecker.org))

3. Update `Caddyfile` on the server:

```
app.soundmaze.com {
    reverse_proxy flask:8000
}
```

4. Restart Caddy:

```bash
docker compose -f docker-compose.prod.yml restart caddy
```

Caddy automatically obtains HTTPS certificates. Within a minute, `https://app.soundmaze.com` should work.

---

## Step 6: Updating the app

```bash
ssh deploy@YOUR_VPS_IP
cd ~/soundmaze
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

For **database migrations**:

```bash
docker compose -f docker-compose.prod.yml exec flask flask db upgrade
```

---

## Useful commands

```bash
# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs (all / specific service)
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f flask

# Shell into flask container
docker compose -f docker-compose.prod.yml exec flask bash

# Run flask CLI commands
docker compose -f docker-compose.prod.yml exec flask flask load-json-book somebook.json

# Restart / stop
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml down

# Stop and DELETE all data
docker compose -f docker-compose.prod.yml down -v
```

---

## Backups

```bash
# Dump database
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U soundmaze soundmaze > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260211.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U soundmaze soundmaze
```

Automate with cron:

```bash
crontab -e
# Daily backup at 3am:
0 3 * * * cd ~/soundmaze && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U soundmaze soundmaze > ~/backups/soundmaze_$(date +\%Y\%m\%d).sql
```

---

## Troubleshooting

**"Waiting for Postgres..." loops forever:**
Check db container: `docker compose -f docker-compose.prod.yml logs db`

**Caddy won't issue HTTPS cert:**
- Verify A record points to VPS IP
- Check ports: `sudo ufw status`
- Check logs: `docker compose -f docker-compose.prod.yml logs caddy`

**App crashes on start:**
Check: `docker compose -f docker-compose.prod.yml logs flask`
Likely a missing env var in `.env`

**Out of disk space:**
`docker system prune -a`
