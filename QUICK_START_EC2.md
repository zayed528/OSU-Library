# 🚀 Quick Start: Deploy SeatSense Backend to AWS EC2

## What You Need

- AWS Account with EC2 access
- Your AWS credentials (Access Key, Secret Key, Session Token)
- Terminal access

## 5-Minute Setup

### 1️⃣ Launch EC2 Instance (AWS Console)

**Go to**: AWS Console → EC2 → Launch Instance

**Configure**:

- **Name**: `seatsense-backend`
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance type**: t2.micro (Free tier)
- **Key pair**: Create/download new .pem file
- **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 8001 (Custom TCP) from anywhere

**Launch** and wait ~1 minute

### 2️⃣ Connect to Your Instance

```bash
# Note your instance's Public IPv4 DNS from EC2 dashboard
# Example: ec2-3-85-123-45.compute-1.amazonaws.com

# Make key secure and connect
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR-EC2-PUBLIC-DNS
```

### 3️⃣ Install Everything (Copy-Paste This)

```bash
# Update & install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y

# Clone your repo
cd ~
git clone https://github.com/zayed528/OSU-Library.git
cd OSU-Library

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4️⃣ Configure AWS Credentials

```bash
# Create .env file
nano .env
```

**Paste this** (replace with YOUR credentials from AWS Learner Lab):

```
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=ASIAU72LGN3UXXXXXXXXX
AWS_SECRET_ACCESS_KEY=4sKtpt3pbT9YsYshKza4XXXXXXXXXXXXXXXXXX
AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjEMj//////////XXXXXXXXXXXXXXXXX
LIBRARY_TABLE=LibraryTables
HOLDS_TABLE=Holds
FORUM_TABLE=ForumPosts
```

**Save**: Ctrl+O, Enter, Ctrl+X

### 5️⃣ Start the Server

```bash
# Make sure you're in venv
source venv/bin/activate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**You should see**:

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

### 6️⃣ Test It Works

**Open new terminal on your Mac**:

```bash
# Replace with YOUR EC2 public IP/DNS
curl http://ec2-3-85-123-45.compute-1.amazonaws.com:8001/health
```

**Expected**: `{"ok":true}`

### 7️⃣ Update Frontend to Use EC2

**Edit** `app/frontend/app.js`:

```javascript
// Change line 2 from:
const API_BASE_URL = "http://localhost:8001/api";

// To (use YOUR EC2 public DNS):
const API_BASE_URL = "http://ec2-3-85-123-45.compute-1.amazonaws.com:8001/api";
```

**Commit and push**:

```bash
git add app/frontend/app.js
git commit -m "Update API URL to EC2 backend"
git push
```

Netlify will auto-deploy in ~30 seconds! ✅

### 8️⃣ Keep Server Running (Production)

Currently the server stops when you close SSH. To keep it running:

**Create systemd service**:

```bash
sudo nano /etc/systemd/system/seatsense.service
```

**Paste** (update paths and credentials):

```ini
[Unit]
Description=SeatSense Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/OSU-Library
Environment="PATH=/home/ubuntu/OSU-Library/venv/bin"
EnvironmentFile=/home/ubuntu/OSU-Library/.env
ExecStart=/home/ubuntu/OSU-Library/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001

[Install]
WantedBy=multi-user.target
```

**Enable it**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable seatsense
sudo systemctl start seatsense

# Check status
sudo systemctl status seatsense
```

Now your server runs 24/7! 🎉

---

## 🆘 Troubleshooting

### Server won't start?

```bash
# Check logs
sudo journalctl -u seatsense -n 50

# Restart service
sudo systemctl restart seatsense
```

### Can't connect from frontend?

1. Check Security Group has port 8001 open
2. Verify EC2 public DNS is correct in app.js
3. Test with curl from your Mac

### AWS credentials expired?

AWS Learner Lab tokens expire every 4 hours. Update .env:

```bash
nano /home/ubuntu/OSU-Library/.env
# Update credentials, then:
sudo systemctl restart seatsense
```

---

## 📊 Your URLs After Deployment

- **Frontend**: https://seatsenseproto.netlify.app
- **Backend API**: http://YOUR-EC2-DNS:8001/api/library/tables
- **Health Check**: http://YOUR-EC2-DNS:8001/health

---

## 💰 Cost

- **Free tier**: First year FREE
- **After free tier**: ~$8-10/month for t2.micro

**Important**: Stop your EC2 instance when not using to save money!

---

## 📝 Quick Reference

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@YOUR-EC2-DNS

# Activate Python environment
source venv/bin/activate

# Start server manually
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Check service status
sudo systemctl status seatsense

# View logs
sudo journalctl -u seatsense -f

# Restart service
sudo systemctl restart seatsense

# Pull latest code
cd ~/OSU-Library
git pull
sudo systemctl restart seatsense
```

---

## ✅ Success Checklist

- [ ] EC2 instance launched and running
- [ ] SSH connection works
- [ ] Python environment setup complete
- [ ] Server responds to curl health check
- [ ] Frontend app.js updated with EC2 URL
- [ ] Changes pushed to GitHub
- [ ] Netlify auto-deployed
- [ ] Dashboard loads on seatsenseproto.netlify.app
- [ ] Systemd service running for 24/7 uptime

---

**Need help?** Check `EC2_SETUP.md` for detailed troubleshooting!
