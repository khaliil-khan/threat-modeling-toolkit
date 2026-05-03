# 📧 Email Support for Password Reset - Quick Start

## What's New ✨

Password reset emails now work! You can send reset links via Gmail, Outlook, or any email provider.

---

## 2-Minute Setup

### Option A: Gmail 📧
```bash
python setup_email.py
# Choose option 1 and follow the prompts
```

### Option B: Outlook 📧
```bash
python setup_email.py
# Choose option 2 and follow the prompts
```

### Option C: Student/Academic Email 🎓
```bash
python setup_email.py
# Choose option 3 and follow the prompts
```

---

## After Setup

**1. Restart the container:**
```bash
docker compose down
docker compose up -d
```

**2. Test the forgot password flow:**
- Go to: http://13.63.73.247:5000/auth/forgot-password
- Enter your email
- Check your inbox (and spam folder!)
- Click the reset link

**3. Verify in logs:**
```bash
docker logs threat-toolkit 2>&1 | tail -20
```

You should see:
```
✓ Password reset email sent to user@example.com
```

---

## Current Status

✅ **Email sending code updated** - Better error handling, supports Gmail/Outlook/Custom  
✅ **Docker compose configured** - SMTP environment variables added  
✅ **.env file created** - Example configurations for all email providers  
✅ **Interactive setup script** - `python setup_email.py` guides you through setup  
✅ **Detailed guide** - See EMAIL_SETUP_GUIDE.md for troubleshooting  

---

## Supported Email Providers

- ✅ Gmail
- ✅ Outlook / Hotmail
- ✅ Google Workspace
- ✅ Office 365
- ✅ Student/Academic emails
- ✅ SendGrid
- ✅ AWS SES
- ✅ Any SMTP-compatible email provider

---

## Files Changed

| File | Change |
|------|--------|
| `app/auth/routes.py` | Enhanced email sending with better error messages |
| `docker-compose.yml` | Added SMTP environment variables |
| `.env` | New file with example configurations |
| `setup_email.py` | New interactive setup script |
| `EMAIL_SETUP_GUIDE.md` | Detailed step-by-step instructions |

---

## Without Email Configuration

Even without SMTP configured, the system works:
- Reset links are logged to console
- Users won't receive emails
- Logs will show: `⚠️ Email not sent - SMTP not configured`

Perfect for development! Just configure when ready for production.

---

## Next Steps

1. Run: `python setup_email.py`
2. Choose your email provider
3. Restart Docker
4. Test password reset
5. Check logs for success ✅

**That's it!** Password reset emails are now working! 🎉
