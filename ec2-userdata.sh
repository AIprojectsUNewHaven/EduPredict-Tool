#!/bin/bash
# EduPredict Pro - Flask EC2 User Data Script
# Deploys Flask app with Gunicorn + Nginx + HTTPS on AWS EC2
# Paste this into "User data" when launching EC2 instance
# App will be live at http://<PUBLIC-IP> after ~5-7 minutes

exec > /var/log/edupredict-deploy.log 2>&1
set -e

echo "=== EduPredict Pro Flask Auto-Deploy ==="
echo "Started: $(date)"

# Update system
echo "Updating system..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl nginx certbot python3-certbot-nginx awscli

# Clone repository
echo "Cloning repository..."
cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

# Install dependencies
echo "Installing dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_PASSWORD=${EDUPREDICT_ADMIN_PASSWORD:-$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(20)))")}

# Write environment file (not world-readable)
cat > /etc/edupredict.env <<ENVEOF
SECRET_KEY=${SECRET_KEY}
EDUPREDICT_ADMIN_PASSWORD=${ADMIN_PASSWORD}
FLASK_ENV=production
ENVEOF
chmod 600 /etc/edupredict.env
chown ubuntu:ubuntu /etc/edupredict.env

echo "Admin password saved to /etc/edupredict.env — record it now."

# Create systemd service for Gunicorn
echo "Creating Gunicorn service..."
cat > /etc/systemd/system/edupredict.service <<'EOF'
[Unit]
Description=EduPredict Pro Flask App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
EnvironmentFile=/etc/edupredict.env
ExecStart=/home/ubuntu/Edupredict-Pro/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 --access-logfile /var/log/edupredict-access.log app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx as reverse proxy with HTTP -> HTTPS redirect
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/edupredict <<'EOF'
server {
    listen 80;
    server_name _;

    # Redirect all HTTP to HTTPS when a domain is configured
    # Remove this block and use the HTTPS server block below once you have a domain + cert
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}

# Uncomment and fill in after running: sudo certbot --nginx -d yourdomain.com
# server {
#     listen 443 ssl;
#     server_name yourdomain.com;
#
#     ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
#
#     location / {
#         proxy_pass http://127.0.0.1:5000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto https;
#         proxy_read_timeout 120s;
#     }
# }
EOF

# Enable Nginx config
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/edupredict /etc/nginx/sites-enabled/

# Set permissions
chown -R ubuntu:ubuntu /home/ubuntu/Edupredict-Pro

# SQLite backup to S3 (runs daily at 2am; set S3_BACKUP_BUCKET env var to enable)
cat > /usr/local/bin/edupredict-backup.sh <<'EOF'
#!/bin/bash
set -e
DB=/home/ubuntu/Edupredict-Pro/instance/edupredict.db
BUCKET=${S3_BACKUP_BUCKET:-""}
if [ -z "$BUCKET" ]; then exit 0; fi
STAMP=$(date +%Y%m%d-%H%M%S)
DEST="s3://${BUCKET}/edupredict-backups/edupredict-${STAMP}.db"
sqlite3 "$DB" ".backup /tmp/edupredict-backup.db"
aws s3 cp /tmp/edupredict-backup.db "$DEST"
rm -f /tmp/edupredict-backup.db
echo "Backup complete: $DEST"
EOF
chmod +x /usr/local/bin/edupredict-backup.sh

# Install backup cron
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/edupredict-backup.sh >> /var/log/edupredict-backup.log 2>&1") | crontab -

# Start services
echo "Starting services..."
systemctl daemon-reload
systemctl enable edupredict
systemctl start edupredict
systemctl restart nginx

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR-INSTANCE-IP")

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "App URL: http://${PUBLIC_IP}"
echo "Health Check: http://${PUBLIC_IP}/health"
echo "Admin credentials: cat /etc/edupredict.env"
echo "For HTTPS: sudo certbot --nginx -d yourdomain.com"
echo "For S3 backups: export S3_BACKUP_BUCKET=your-bucket-name"
echo "Finished: $(date)"
echo ""
echo "To check status: sudo systemctl status edupredict"
echo "To view logs: sudo journalctl -u edupredict -f"
