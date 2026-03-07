#!/bin/bash
# EduPredict Pro - EC2 User Data Script
# Paste this into "User data" when launching an EC2 instance.
# The app auto-deploys on boot. No SSH needed.
# After ~3-5 minutes, visit http://<PUBLIC-IP>:8501

exec > /var/log/edupredict-deploy.log 2>&1
set -e

echo "=== EduPredict Pro Auto-Deploy ==="
echo "Started: $(date)"

apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

python3 -m pip install --break-system-packages -r requirements.txt

cat > /etc/systemd/system/edupredict.service <<SVCEOF
[Unit]
Description=EduPredict Pro Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
ExecStart=/usr/bin/python3 -m streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
SVCEOF

chown -R ubuntu:ubuntu /home/ubuntu/Edupredict-Pro

systemctl daemon-reload
systemctl enable edupredict
systemctl start edupredict

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "UNKNOWN")
echo "=== Deploy Complete ==="
echo "App URL: http://${PUBLIC_IP}:8501"
echo "Finished: $(date)"
