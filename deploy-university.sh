#!/bin/bash
# EduPredict Pro - University VM Deploy Script
# VM: 10.103.9.47 (CIT lab — accessible from Buckman 233C or Maxcy 218)
#
# HOW TO USE:
#   1. SSH into the VM:  ssh <your-cit-username>@10.103.9.47
#   2. Run this script:  bash deploy-university.sh
#
# Or copy-paste each section manually step by step.

set -e
echo "=== EduPredict Pro - University VM Deployment ==="
echo "Target: 10.103.9.47"
echo ""

# -----------------------------------------------------------------------
# 1. System packages
# -----------------------------------------------------------------------
echo "[1/7] Installing system packages..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git nginx

# -----------------------------------------------------------------------
# 2. Clone repo
# -----------------------------------------------------------------------
echo "[2/7] Cloning repository..."
cd ~
if [ -d "Edupredict-Pro" ]; then
    echo "  Repo already exists — pulling latest..."
    cd Edupredict-Pro
    git pull
else
    git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
    cd Edupredict-Pro
fi

# -----------------------------------------------------------------------
# 3. Python virtual environment + dependencies
# -----------------------------------------------------------------------
echo "[3/7] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# -----------------------------------------------------------------------
# 4. Environment variables
# -----------------------------------------------------------------------
echo "[4/7] Configuring environment..."

# Generate a random secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Set your admin password here (or it will be auto-generated)
ADMIN_PASSWORD=${EDUPREDICT_ADMIN_PASSWORD:-$(python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits
print(''.join(secrets.choice(chars) for _ in range(16)))
")}

cat > .env <<ENVEOF
SECRET_KEY=${SECRET_KEY}
EDUPREDICT_ADMIN_PASSWORD=${ADMIN_PASSWORD}
FLASK_ENV=production
ENVEOF
chmod 600 .env

echo ""
echo "  *** SAVE THESE CREDENTIALS ***"
echo "  Admin email:    admin@edupredict.local"
echo "  Admin password: ${ADMIN_PASSWORD}"
echo "  (also saved in .env)"
echo ""

# -----------------------------------------------------------------------
# 5. Initialize the database
# -----------------------------------------------------------------------
echo "[5/7] Initializing database..."
export SECRET_KEY EDUPREDICT_ADMIN_PASSWORD=${ADMIN_PASSWORD} FLASK_ENV=production
python3 -c "
from app import app, db, init_db
import os
os.environ['EDUPREDICT_ADMIN_PASSWORD'] = '${ADMIN_PASSWORD}'
with app.app_context():
    db.create_all()
    init_db()
print('  Database initialized.')
"

# Fetch enrichment data
echo "  Fetching supplementary data..."
python3 data/fetch_enrichment.py 2>&1 | tail -10

# -----------------------------------------------------------------------
# 6. Systemd service
# -----------------------------------------------------------------------
echo "[6/7] Creating systemd service..."

DEPLOY_DIR=$(pwd)
VENV_DIR="${DEPLOY_DIR}/venv"
USER=$(whoami)

sudo tee /etc/systemd/system/edupredict.service > /dev/null <<SVCEOF
[Unit]
Description=EduPredict Pro Flask Application
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${DEPLOY_DIR}
EnvironmentFile=${DEPLOY_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn -w 2 -b 127.0.0.1:5000 --timeout 120 --access-logfile /tmp/edupredict-access.log app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable edupredict
sudo systemctl restart edupredict

# -----------------------------------------------------------------------
# 7. Nginx reverse proxy
# -----------------------------------------------------------------------
echo "[7/7] Configuring Nginx..."

sudo tee /etc/nginx/sites-available/edupredict > /dev/null <<'NGINXEOF'
server {
    listen 80;
    server_name 10.103.9.47 _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
NGINXEOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/edupredict /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# -----------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------
echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "  App URL (from lab):  http://10.103.9.47"
echo "  Health check:        http://10.103.9.47/health"
echo "  Admin login:         admin@edupredict.local"
echo "  Admin password:      ${ADMIN_PASSWORD}"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status edupredict    # check if running"
echo "    sudo journalctl -u edupredict -f    # live logs"
echo "    sudo systemctl restart edupredict   # restart after code change"
echo ""
echo "  To update the app:"
echo "    cd ~/Edupredict-Pro && git pull && sudo systemctl restart edupredict"
