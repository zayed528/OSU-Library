# AWS EC2 Deployment Guide for SeatSense Backend

## Step 1: Launch EC2 Instance

1. Go to AWS Console → EC2 → Launch Instance
2. **Name**: `seatsense-backend`
3. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance type**: t2.micro (Free tier)
5. **Key pair**: Create new or use existing (download .pem file!)
6. **Network settings**:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere (0.0.0.0/0)
   - Allow Custom TCP (port 8001) from anywhere (0.0.0.0/0)
7. **Storage**: 8 GB (default)
8. Click **Launch Instance**

## Step 2: Connect to EC2

```bash
# Make key file secure
chmod 400 your-key.pem

# SSH into instance (replace with your instance's public DNS)
ssh -i your-key.pem ubuntu@ec2-XX-XX-XX-XX.compute-1.amazonaws.com
```

## Step 3: Install Dependencies on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3-pip python3-venv -y

# Install git
sudo apt install git -y

# Clone your repository
git clone https://github.com/zayed528/OSU-Library.git
cd OSU-Library

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## Step 4: Configure AWS Credentials

```bash
# Create .env file with AWS credentials
nano .env
```

Add these lines (replace with your actual credentials):

```
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
LIBRARY_TABLE=LibraryTables
HOLDS_TABLE=Holds
FORUM_TABLE=ForumPosts
```

**Important**: For production, use IAM roles instead of hardcoded credentials!

## Step 5: Test the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run server manually to test
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Test in another terminal (from your local machine)
curl http://your-ec2-public-ip:8001/health
```

## Step 6: Set Up as Background Service (Production)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/seatsense.service
```

Add this content:

```ini
[Unit]
Description=SeatSense FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/OSU-Library
Environment="PATH=/home/ubuntu/OSU-Library/venv/bin"
Environment="AWS_DEFAULT_REGION=us-east-1"
Environment="AWS_ACCESS_KEY_ID=your_key"
Environment="AWS_SECRET_ACCESS_KEY=your_secret"
Environment="LIBRARY_TABLE=LibraryTables"
Environment="HOLDS_TABLE=Holds"
Environment="FORUM_TABLE=ForumPosts"
ExecStart=/home/ubuntu/OSU-Library/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable seatsense
sudo systemctl start seatsense

# Check status
sudo systemctl status seatsense

# View logs
sudo journalctl -u seatsense -f
```

## Step 7: Update Frontend to Use EC2 Backend

Once your EC2 instance is running, update your frontend:

1. Note your EC2 public IP or DNS: `ec2-XX-XX-XX-XX.compute-1.amazonaws.com`

2. Edit `app/frontend/app.js`:

```javascript
// Change from:
const API_BASE_URL = "http://localhost:8001/api";

// To:
const API_BASE_URL = "http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8001/api";
```

3. Push to GitHub:

```bash
git add app/frontend/app.js
git commit -m "Update API URL to EC2 backend"
git push
```

4. Netlify will auto-deploy with the new API URL!

## Step 8: (Optional) Set Up Domain with SSL

For production, you should:

1. **Get a domain** (Route 53 or other registrar)
2. **Set up Nginx** as reverse proxy
3. **Install SSL certificate** (Let's Encrypt)
4. **Point domain** to EC2 (Route 53 A record)

Then your API URL would be: `https://api.seatsense.com`

## Troubleshooting

### Check if server is running:

```bash
sudo systemctl status seatsense
```

### View logs:

```bash
sudo journalctl -u seatsense -n 50
```

### Restart service:

```bash
sudo systemctl restart seatsense
```

### Test API from EC2:

```bash
curl http://localhost:8001/health
```

### Security Group Issues:

- Make sure port 8001 is open in EC2 Security Group
- Allow inbound traffic from 0.0.0.0/0 on port 8001

## Cost Estimate

- **t2.micro EC2**: Free tier (1 year) or ~$8/month after
- **Data transfer**: Minimal for this app
- **Total**: FREE for 1 year, then ~$8-10/month

## Important Notes

1. **IAM Roles**: For production, attach an IAM role to EC2 instead of hardcoding credentials
2. **Security Groups**: Lock down port 8001 to only Netlify IPs if possible
3. **Monitoring**: Set up CloudWatch alarms for instance health
4. **Backups**: DynamoDB handles this, but document your EC2 setup
5. **Auto-scaling**: For higher traffic, consider AWS App Runner or Elastic Beanstalk instead

---

## Quick Reference Commands

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-public-dns

# Activate venv
source venv/bin/activate

# Check service status
sudo systemctl status seatsense

# Restart service
sudo systemctl restart seatsense

# View logs
sudo journalctl -u seatsense -f

# Test API
curl http://localhost:8001/health
```
