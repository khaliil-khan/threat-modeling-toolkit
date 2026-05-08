# Threat Modeling Toolkit

A professional web application for identifying, documenting, and managing security threats using industry-standard methodologies.

## Features

- **Threat Modeling** — Create models using STRIDE, PASTA, or DREAD methodologies
- **DREAD Scoring** — Quantify risk with automated score calculation (Critical/High/Medium/Low)
- **DFD Builder** — Interactive drag-and-drop Data Flow Diagram editor with resizable elements
- **Dashboard** — Visual analytics with charts for threat distribution and risk levels
- **User Management** — Role-based access control (Admin/User), rate-limited authentication
- **Password Reset** — Secure token-based reset with email delivery or console fallback
- **PDF Reports** — Export threat models as downloadable PDF documents
- **Admin Panel** — View all users, manage roles, delete accounts

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask, SQLAlchemy, Gunicorn |
| Database | PostgreSQL (production), SQLite (development) |
| Frontend | Jinja2, CoreUI 4.3, Chart.js, Vanilla JS |
| Security | CSP with nonces, CSRF protection, PBKDF2 hashing, rate limiting |
| Deployment | Docker, Nginx, AWS EC2, Let's Encrypt SSL |

## Quick Start (Development)

```bash
# Clone
git clone https://github.com/khaliil-khan/threat-modeling-toolkit.git
cd threat-modeling-toolkit

# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python run.py
```

## Deployment (Docker)

```bash
cp .env.example .env
# Edit .env (set SECRET_KEY, APP_ENV=production, DATABASE_URL)

docker-compose up -d --build
```

## Security

- Content Security Policy with per-request nonces
- CSRF protection on all forms
- Rate limiting (login, registration, password reset)
- Secure session cookies (HttpOnly, Secure, SameSite)
- HSTS, X-Frame-Options, X-Content-Type-Options headers
- SQL injection prevention via ORM parameterized queries
- XSS prevention via Jinja2 auto-escaping

## Contributors

| Name | Role |
|------|------|
| Khalil Khan | Auth, admin panel, project lead |
| Rayhan | DFD builder, CSP security, UI design |
| Waleed Ahmad | Testing, SMTP validation, security hardening |

## License

This project is for educational purposes — PAF-IAST Secure Software Design & Development course.
