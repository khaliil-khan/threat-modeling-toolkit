#!/usr/bin/env python3
"""
Interactive Email Configuration Setup for Threat Toolkit
Guides users through setting up Gmail, Outlook, or other email providers.
"""

import os
import sys
from pathlib import Path

def setup_gmail():
    """Guide user through Gmail setup"""
    print("\n" + "="*60)
    print("📧 GMAIL SETUP GUIDE")
    print("="*60)
    print("""
Step 1: Enable 2-Step Verification
  ✓ Go to: https://myaccount.google.com/security
  ✓ Click "2-Step Verification"
  ✓ Complete the verification process

Step 2: Generate App Password
  ✓ Go to: https://myaccount.google.com/apppasswords
  ✓ Select "Mail" and "Windows Computer"
  ✓ Google will show a 16-character password with spaces
  ✓ Copy this password exactly as shown

Step 3: Enter your details below
""")
    
    email = input("📧 Gmail address (e.g., user@gmail.com): ").strip()
    password = input("🔑 App password (16 chars with spaces): ").strip()
    
    return {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': email,
        'SENDER_PASSWORD': password
    }

def setup_outlook():
    """Guide user through Outlook setup"""
    print("\n" + "="*60)
    print("📧 OUTLOOK/HOTMAIL SETUP GUIDE")
    print("="*60)
    print("""
Step 1: Enable 2-Step Verification
  ✓ Go to: https://account.microsoft.com/security
  ✓ Click "Advanced security options"
  ✓ Enable 2-Step Verification

Step 2: Create App Password
  ✓ Go to: https://account.microsoft.com/security
  ✓ Click "App passwords"
  ✓ Select "Mail" and "Windows"
  ✓ Copy the generated password (with dashes)

Step 3: Enter your details below
""")
    
    email = input("📧 Outlook email (e.g., user@outlook.com): ").strip()
    password = input("🔑 App password (with dashes): ").strip()
    
    return {
        'SMTP_SERVER': 'smtp-mail.outlook.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': email,
        'SENDER_PASSWORD': password
    }

def setup_academic():
    """Guide user through academic email setup"""
    print("\n" + "="*60)
    print("📧 ACADEMIC/STUDENT EMAIL SETUP")
    print("="*60)
    print("""
Most universities use Office 365 (Outlook) or Google Workspace.

Step 1: Contact Your University IT Support
  ✓ Ask for SMTP server settings
  ✓ Ask if you need 2FA for app passwords
  ✓ Ask if your password needs special handling

Common Settings:
  • Office 365: smtp-mail.outlook.com:587
  • Google Workspace: smtp.gmail.com:587
  • Custom Domain: Usually provided by IT

Step 2: Generate/Request App Password
  ✓ Follow your university's process
  ✓ Usually similar to Gmail or Outlook

Step 3: Enter your details below
""")
    
    email = input("📧 University email (e.g., name@university.edu): ").strip()
    server = input("🔗 SMTP server (e.g., smtp-mail.outlook.com): ").strip()
    password = input("🔑 App password or your university password: ").strip()
    port = input("🔌 SMTP port (default 587): ").strip() or "587"
    
    return {
        'SMTP_SERVER': server,
        'SMTP_PORT': port,
        'SENDER_EMAIL': email,
        'SENDER_PASSWORD': password
    }

def setup_custom():
    """Guide user through custom email setup"""
    print("\n" + "="*60)
    print("📧 CUSTOM EMAIL PROVIDER SETUP")
    print("="*60)
    print("""
Configure any email provider (SendGrid, AWS SES, Company Email, etc.)

Enter your SMTP settings:
""")
    
    server = input("🔗 SMTP server (e.g., smtp.sendgrid.net): ").strip()
    port = input("🔌 SMTP port (usually 587): ").strip()
    email = input("📧 From email address (sender): ").strip()
    password = input("🔑 SMTP password or API key: ").strip()
    
    return {
        'SMTP_SERVER': server,
        'SMTP_PORT': port,
        'SENDER_EMAIL': email,
        'SENDER_PASSWORD': password
    }

def write_env_file(config):
    """Write configuration to .env file"""
    env_path = Path(__file__).parent / '.env'
    
    # Read existing .env if it exists
    existing = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing[key.strip()] = value.strip()
    
    # Update with new config
    existing.update(config)
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.write("# Environment Configuration for Threat Toolkit\n\n")
        f.write("# Flask Configuration\n")
        f.write(f"SECRET_KEY={existing.get('SECRET_KEY', 'your-secret-key-here')}\n")
        f.write(f"APP_ENV={existing.get('APP_ENV', 'development')}\n")
        f.write(f"ADMIN_EMAILS={existing.get('ADMIN_EMAILS', '')}\n\n")
        f.write("# Email Configuration\n")
        f.write(f"SMTP_SERVER={config['SMTP_SERVER']}\n")
        f.write(f"SMTP_PORT={config['SMTP_PORT']}\n")
        f.write(f"SENDER_EMAIL={config['SENDER_EMAIL']}\n")
        f.write(f"SENDER_PASSWORD={config['SENDER_PASSWORD']}\n")
    
    print(f"\n✅ Configuration saved to .env")
    return True

def show_menu():
    """Show main menu"""
    print("\n" + "="*60)
    print("📧 THREAT TOOLKIT - EMAIL CONFIGURATION SETUP")
    print("="*60)
    print("""
Which email provider do you want to use?

1. 📧 Gmail (with App Password)
2. 📧 Outlook/Hotmail (with App Password)
3. 🎓 Student/Academic Email (University)
4. ⚙️  Custom Email Provider
5. ❌ Cancel

""")
    
    choice = input("Select option (1-5): ").strip()
    return choice

def main():
    """Main entry point"""
    print("\n🚀 Threat Toolkit Email Configuration Setup")
    print("This will configure password reset emails for your application.\n")
    
    choice = show_menu()
    
    config = None
    if choice == '1':
        config = setup_gmail()
    elif choice == '2':
        config = setup_outlook()
    elif choice == '3':
        config = setup_academic()
    elif choice == '4':
        config = setup_custom()
    elif choice == '5':
        print("\n❌ Setup cancelled.")
        return
    else:
        print("\n❌ Invalid option. Please run again and select 1-5.")
        return
    
    if config:
        print("\n📋 Configuration Summary:")
        print(f"  SMTP Server: {config['SMTP_SERVER']}")
        print(f"  SMTP Port: {config['SMTP_PORT']}")
        print(f"  From Email: {config['SENDER_EMAIL']}")
        print(f"  Password: {'*' * len(config['SENDER_PASSWORD'])}")
        
        confirm = input("\nSave this configuration? (y/n): ").strip().lower()
        
        if confirm == 'y':
            write_env_file(config)
            
            print("\n" + "="*60)
            print("✅ EMAIL CONFIGURATION COMPLETE!")
            print("="*60)
            print("""
Next steps:

1. Restart Docker container:
   docker compose down
   docker compose up -d

2. Test password reset:
   • Go to http://localhost:5000/auth/forgot-password
   • Enter your email
   • Check your inbox (and spam folder!)
   • Click the reset link in the email

3. Verify in Docker logs:
   docker logs threat-toolkit 2>&1 | grep -E "(✓|✗)"

📖 For detailed troubleshooting, see EMAIL_SETUP_GUIDE.md
""")
        else:
            print("\n❌ Configuration not saved.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
