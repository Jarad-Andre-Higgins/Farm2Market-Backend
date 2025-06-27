# 🚀 Farm2Market - Railway Deployment Guide

## ⚡ Quick Deployment (10-15 minutes)

### 📋 **Prerequisites:**
- GitHub account
- Railway account (free signup at railway.app)

### 🔧 **Step 1: Prepare Your Code**
✅ All files are ready in your AGRIPORT folder:
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment commands
- `railway.json` - Railway configuration
- `settings_production.py` - Production settings

### 🌐 **Step 2: Deploy to Railway**

1. **Sign up at Railway.app** (free)
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Upload/push your AGRIPORT folder to GitHub

3. **Configure Environment Variables**
   ```
   DJANGO_SETTINGS_MODULE=farm2market_backend.settings_production
   DJANGO_SECRET_KEY=your-secret-key-here
   DEBUG=False
   ```

4. **Add MySQL Database**
   - In Railway dashboard, click "Add Service"
   - Select "MySQL"
   - Railway will automatically provide DATABASE_URL

5. **Deploy**
   - Railway will automatically build and deploy
   - You'll get a URL like: https://your-app.railway.app

### 🎯 **Step 3: Access Your Application**

**Your Farm2Market will be available at:**
- **Main Site**: https://your-app.railway.app/
- **Admin Panel**: https://your-app.railway.app/admin/
- **API**: https://your-app.railway.app/api/

**Default Admin Credentials:**
- Email: admin@farm2market.com
- Password: admin123

### 📱 **Step 4: Test for Your Presentation**

✅ **Test these features:**
- [ ] Admin login works
- [ ] Farmer registration
- [ ] Buyer registration  
- [ ] Product listings
- [ ] API endpoints respond
- [ ] Frontend loads properly

### 🔒 **Security Notes:**
- Change admin password after deployment
- Your app will have HTTPS automatically
- Database is secure and isolated

### 📞 **Support:**
If you encounter issues:
1. Check Railway logs in dashboard
2. Verify environment variables
3. Ensure all files are uploaded correctly

**Your app will be live and ready for your class presentation!** 🎓
