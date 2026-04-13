# AWS EC2 Deployment (Flask)

EduPredict Pro runs as **Flask + Gunicorn** behind **Nginx** on port **80** (app on **5000** locally on the instance). Use the same flow as in `README.md`, or paste **`ec2-userdata.sh`** into the EC2 launch **User data** field for an automated install.

## Security group

| Type | Port | Source   |
|------|------|----------|
| SSH  | 22   | My IP    |
| HTTP | 80   | 0.0.0.0/0 |

Do **not** use port 8501; that was legacy Streamlit documentation.

## After the instance boots

1. Wait 3 to 5 minutes for cloud-init.
2. Open `http://<PUBLIC-IP>/` in a browser.
3. Logs: `sudo tail -f /var/log/edupredict-deploy.log` (user-data) or `sudo journalctl -u edupredict -f` (service).

## Docker (optional)

```bash
docker build -t edupredict-pro .
docker run -p 5000:5000 edupredict-pro
```

The container exposes Gunicorn on **5000** (see `Dockerfile`).

## Reference scripts

- `ec2-userdata.sh` -- full Ubuntu + Nginx + systemd + clone + `pip` + Gunicorn.
- `README.md` -- student lab steps and systemd unit examples.
