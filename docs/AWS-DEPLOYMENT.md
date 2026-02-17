# AWS EC2 Deployment Guide

This guide walks you through deploying ExamForge on an AWS EC2 instance using Docker.

## Prerequisites

- AWS account with EC2 access
- Basic familiarity with AWS Console
- SSH key pair for EC2 access
- Google Gemini API key

## Step 1: Launch EC2 Instance

### 1.1 Create Instance

1. Log into AWS Console and navigate to EC2
2. Click **"Launch Instance"**
3. Configure instance:
   - **Name**: ExamForge-Production
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type**: t3.micro (1 vCPU, 1 GB RAM)
   - **Key pair**: Select existing or create new SSH key
   - **Network settings**:
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere (0.0.0.0/0)
     - Allow HTTPS (port 443) from anywhere (optional for future)
   - **Storage**: 20 GB gp3 (minimum recommended)

4. Click **"Launch Instance"**

### 1.2 Allocate Elastic IP (Recommended)

1. Navigate to **Elastic IPs** in EC2 dashboard
2. Click **"Allocate Elastic IP address"**
3. Associate the Elastic IP with your instance
4. Note your **Public IP address** - you'll use this to access the application

## Step 2: Connect to Your Instance

```bash
# SSH into your instance (replace with your key and IP)
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## Step 3: Initial Server Setup

### 3.1 Run Setup Script

```bash
# Download the setup script
wget https://raw.githubusercontent.com/YOUR_USERNAME/ExamForge/main/deploy/setup-ec2.sh

# Or if you've cloned the repo:
git clone https://github.com/YOUR_USERNAME/ExamForge.git
cd ExamForge

# Run the setup script
sudo bash deploy/setup-ec2.sh
```

This script will:
- Update system packages
- Install Docker and Docker Compose
- Configure firewall (UFW)
- Set up 2GB swap file (important for t3.micro)
- Configure security settings

**Note**: After the script completes, **log out and log back in** for Docker group changes to take effect.

```bash
exit
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3.2 Verify Installation

```bash
# Check Docker
docker --version

# Check Docker Compose
docker-compose --version

# Test Docker without sudo
docker ps
```

## Step 4: Configure Application

### 4.1 Clone Repository (if not done already)

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/ExamForge.git
cd ExamForge
```

### 4.2 Setup Environment Variables

```bash
# Copy production environment template
cp .env.production .env

# Edit .env file
nano .env
```

Update the following in `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Save and exit (Ctrl+X, Y, Enter)

## Step 5: Deploy Application

### 5.1 Run Deployment Script

```bash
# Make sure you're in the ExamForge directory
cd ~/ExamForge

# Run deployment
bash deploy/deploy.sh
```

This script will:
- Build Docker images
- Start containers
- Run health checks
- Display container status

### 5.2 Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl http://localhost/health
```

## Step 6: Access Your Application

Open your browser and navigate to:
```
http://YOUR_EC2_PUBLIC_IP
```

You should see the ExamForge application!

## Managing Your Application

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Application

```bash
docker-compose -f docker-compose.prod.yml restart
```

### Stop Application

```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Application

```bash
# Pull latest changes
git pull

# Redeploy
bash deploy/deploy.sh
```

### Access Container Shell

```bash
# Backend
docker-compose -f docker-compose.prod.yml exec backend bash

# Frontend
docker-compose -f docker-compose.prod.yml exec frontend sh
```

## Monitoring

### System Resources

```bash
# CPU and memory usage
htop

# Docker stats
docker stats

# Disk usage
df -h

# Docker disk usage
docker system df
```

### Application Health

```bash
# Frontend health check
curl http://localhost/health

# Backend API check
curl http://localhost:8000/
```

## Troubleshooting

### Application won't start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check memory
free -h
```

### Out of memory errors

```bash
# Verify swap is enabled
swapon --show

# Check memory usage
free -h

# Restart containers to free memory
docker-compose -f docker-compose.prod.yml restart
```

### Port already in use

```bash
# Check what's using port 80
sudo lsof -i :80

# Stop other web servers if any
sudo systemctl stop apache2  # if Apache is running
sudo systemctl stop nginx    # if standalone Nginx is running
```

### Can't access from browser

1. **Check Security Group**:
   - Ensure port 80 is open in AWS Security Group
   - Source should be `0.0.0.0/0` for public access

2. **Check Firewall**:
   ```bash
   sudo ufw status
   # Should show port 80 allowed
   ```

3. **Check containers are running**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

### File upload fails

```bash
# Check storage permissions
ls -la backend/storage/

# Create directories if missing
mkdir -p backend/storage/uploads backend/storage/generated
chmod -R 777 backend/storage/
```

## Maintenance

### Regular Updates

```bash
# Update system packages (monthly recommended)
sudo apt update && sudo apt upgrade -y

# Update application
cd ~/ExamForge
git pull
bash deploy/deploy.sh
```

### Backup Storage

```bash
# Backup uploaded files and generated PDFs
tar -czf examforge-backup-$(date +%Y%m%d).tar.gz \
  -C backend/storage .

# Download backup to your local machine
scp -i /path/to/key.pem \
  ubuntu@YOUR_EC2_IP:~/ExamForge/examforge-backup-*.tar.gz \
  ./
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (be careful!)
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

## Security Best Practices

1. **Use Elastic IP**: Prevents IP changes on instance restart
2. **Regular Updates**: Keep system and Docker updated
3. **Limit SSH Access**: Only allow SSH from your IP in Security Group
4. **Strong SSH Keys**: Use strong key pairs, never expose private keys
5. **Environment Variables**: Never commit `.env` to git
6. **Monitoring**: Regularly check logs for suspicious activity

## Cost Optimization

### t3.micro Free Tier
- 750 hours/month free for first 12 months
- 1 GB RAM, 1 vCPU
- Suitable for low-traffic applications

### Beyond Free Tier
- t3.micro: ~$7.50/month
- Consider Reserved Instances for long-term savings
- Monitor CloudWatch for usage patterns

## Next Steps

### Future Enhancements

1. **Add SSL/HTTPS**: Use Let's Encrypt with Certbot when you get a domain
2. **Add Database**: PostgreSQL for production data storage
3. **Add Redis**: For caching and session management
4. **Setup CI/CD**: Automate deployments with GitHub Actions
5. **Add Monitoring**: CloudWatch, Prometheus, or Grafana
6. **Load Balancing**: Use ALB for multiple instances

---

## Quick Reference

```bash
# Start application
docker-compose -f docker-compose.prod.yml up -d

# Stop application
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart
docker-compose -f docker-compose.prod.yml restart

# Rebuild and deploy
bash deploy/deploy.sh

# Check health
curl http://localhost/health
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Review this guide's troubleshooting section
- Check AWS EC2 instance status in console
- Verify Security Group settings
