# Prompt: Explain My Threat Modeling Toolkit Project

Use this prompt with any AI to get a full understanding of the project:

---

## PROMPT START

I need you to understand my university group project completely — the concept, architecture, security implementation, team roles, and deployment. Here's everything:

---

### PROJECT OVERVIEW

**Name:** Threat Modeling Toolkit  
**Type:** Full-stack secure web application (university group project)  
**Purpose:** A professional tool for security professionals and students to create threat models, categorize threats using STRIDE methodology, score them using DREAD methodology, build Data Flow Diagrams (DFD), and generate PDF reports.  
**Live URL:** https://threat-toolkit.duckdns.org  
**GitHub:** https://github.com/khaliil-khan/threat-modeling-toolkit  
**Deployed on:** AWS EC2 (Ubuntu 24.04) inside Docker containers with Nginx reverse proxy and HTTPS via Let's Encrypt  

---

### WHAT THE APP DOES (User Flow)

1. User registers an account (password hashed with PBKDF2-SHA256, validated for complexity)
2. User logs in (rate-limited, session-protected, CSRF-protected)
3. User creates a **Threat Model** (a container/project for organizing threats)
4. User selects methodology: **STRIDE**, **PASTA**, or **DREAD**
5. User adds individual **Threats** to the model:
   - Assigns a STRIDE category (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege)
   - Rates 5 DREAD factors on a 1-5 scale (Damage, Reproducibility, Exploitability, Affected Users, Discoverability)
   - System auto-calculates DREAD score and assigns risk level (Critical/High/Medium/Low)
   - User writes countermeasures/mitigations
6. User views **Dashboard** with analytics: risk matrix visualization, STRIDE distribution chart, threat statistics
7. User builds **Data Flow Diagrams** (interactive canvas editor with processes, data stores, external entities, flows)
8. User exports **PDF Reports** of their threat models
9. User can search/filter threats, export CSV, get executive summaries
10. Admin users can manage all users via admin panel

---

### TEAM ROLES & CONTRIBUTIONS

| Team Member | Role | What They Built |
|-------------|------|-----------------|
| **Khalil** | Team Lead + Authentication & Security | Login/Register system, password hashing (PBKDF2-SHA256), rate limiting (sliding window algorithm), RBAC (role-based access control with `@roles_required` decorator), session security (HttpOnly, Secure, SameSite cookies), CSRF protection, security headers (CSP, X-Frame-Options, HSTS), password reset with secure email tokens, open redirect prevention, admin panel, project deployment on AWS EC2 with Docker + Nginx + HTTPS |
| **Saad** | Dashboard & Analytics | Dashboard page with threat statistics, risk matrix canvas visualization (5x5 heatmap with threat points plotted by exploitability vs damage), STRIDE distribution doughnut chart (Chart.js), metric cards (total threats, critical count, open count), responsive layout |
| **Waleed** | Threat Management (Core Module) | Threat model CRUD operations, threat creation with STRIDE/DREAD forms, DREAD auto-calculation algorithm (`calculate_dread()` method), risk level assignment logic, threat analytics module (`ThreatAnalytics`, `ThreatFilter`, `ThreatReporter` classes), search/filter functionality, JSON/CSV/text report exports, executive summary generation |
| **Rayhan** | DFD Editor & PDF Reports | Interactive Data Flow Diagram canvas editor (HTML5 Canvas with JavaScript), DFD element types (Process, Data Store, External Entity, Flow with arrows), canvas save/load via JSON, PDF report generation using ReportLab library (A4 format with threat details, DREAD scores, risk levels) |

---

### TECHNOLOGY STACK

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend Language | Python 3.11 | Industry standard for web security tools |
| Web Framework | Flask + Blueprints | Lightweight, modular, good for learning |
| Database | SQLite (dev) / PostgreSQL (prod-ready) | Simple for dev, scalable for production |
| ORM | SQLAlchemy | Prevents SQL injection, clean data access |
| Authentication | Flask-Login | Session management, remember-me |
| CSRF Protection | Flask-WTF (CSRFProtect) | Prevents cross-site request forgery |
| Password Hashing | Werkzeug (PBKDF2-SHA256, 260K iterations) | Industry-standard one-way hashing |
| Forms | WTForms | Server-side validation |
| Frontend | Jinja2 templates + CoreUI (Bootstrap-based) | Professional dark-themed UI |
| Charts | Chart.js | STRIDE distribution visualization |
| PDF Generation | ReportLab | Professional PDF exports |
| Canvas Editor | HTML5 Canvas + vanilla JavaScript | DFD diagram builder |
| WSGI Server | Gunicorn | Production-grade multi-worker server |
| Containerization | Docker + Docker Compose | Consistent deployment |
| Cloud Hosting | AWS EC2 (t2.micro, Ubuntu 24.04) | Free tier eligible |
| Reverse Proxy | Nginx | HTTPS termination, security |
| SSL/TLS | Let's Encrypt (Certbot) | Free HTTPS certificates |
| DNS | DuckDNS | Free dynamic DNS |
| Database (prod) | PostgreSQL 16 (Docker container or AWS RDS ready) | Concurrent writes, proper production DB |

---

### ARCHITECTURE

```
Internet → DuckDNS (threat-toolkit.duckdns.org)
    → AWS EC2 (52.72.57.162)
        → Nginx (port 443/80, HTTPS termination)
            → Docker Container: Gunicorn + Flask App (port 5000)
                → SQLite/PostgreSQL Database
```

**Application Structure (Flask Blueprints):**
```
app/
├── __init__.py          → App factory, security config, headers
├── models.py            → User, ThreatModel, Threat, DFDData (SQLAlchemy)
├── auth/                → Authentication blueprint (Khalil)
│   ├── routes.py        → Login, register, logout, forgot/reset password, admin
│   └── forms.py         → Registration, login, password reset forms
├── threats/             → Threat management blueprint (Waleed)
│   ├── routes.py        → CRUD, analytics, search, reports, exports
│   └── forms.py         → ThreatModelForm, ThreatForm with DREAD sliders
├── dashboard/           → Dashboard blueprint (Saad)
│   └── routes.py        → Statistics aggregation, risk matrix data
├── dfd/                 → DFD editor blueprint (Rayhan)
│   └── routes.py        → Canvas save/load with JSON validation
├── reports/             → PDF reports blueprint (Rayhan)
│   └── routes.py        → PDF generation with ReportLab
├── utils/
│   └── threat_analytics.py → ThreatAnalytics, ThreatFilter, ThreatReporter
├── static/
│   ├── css/style.css    → Dark glassmorphism theme
│   └── js/              → app.js, charts.js, dfd_editor.js, risk_matrix.js
└── templates/           → Jinja2 HTML templates
```

---

### SECURITY FEATURES IMPLEMENTED (Key Selling Points)

1. **Password Hashing** — PBKDF2-SHA256 with automatic salting (260K iterations)
2. **Rate Limiting** — Sliding window algorithm on login (5 attempts/5min per IP:username), register (5/5min per IP), password reset (3/5min per IP)
3. **CSRF Protection** — Flask-WTF tokens on all forms, 30-minute expiry
4. **Session Security** — HttpOnly, Secure, SameSite=Lax cookies, 8-hour lifetime, strong session protection
5. **Security Headers** — X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy, Permissions-Policy, HSTS
6. **RBAC** — Role-based access control (user/admin roles, `@roles_required` decorator)
7. **IDOR Prevention** — Every route checks `model.user_id == current_user.id` before access
8. **SQL Injection Prevention** — SQLAlchemy ORM (parameterized queries, never raw SQL)
9. **XSS Prevention** — Jinja2 auto-escaping, Content Security Policy
10. **Open Redirect Prevention** — `_is_safe_next_url()` validates redirect targets
11. **Password Reset Tokens** — SHA-256 hashed in DB, 1-hour expiry, constant-time comparison
12. **Input Validation** — Server-side length limits, regex whitelist on usernames, password complexity
13. **SRI (Subresource Integrity)** — Integrity hashes on CDN resources
14. **Non-root Docker** — Container runs as unprivileged user

---

### DREAD SCORING SYSTEM (Core Algorithm)

```python
def calculate_dread(self):
    self.dread_score = round((
        self.damage + 
        self.reproducibility + 
        self.exploitability + 
        self.affected_users + 
        self.discoverability
    ) / 5, 2)
    
    if self.dread_score >= 4:   self.risk_level = 'Critical'
    elif self.dread_score >= 3: self.risk_level = 'High'
    elif self.dread_score >= 2: self.risk_level = 'Medium'
    else:                       self.risk_level = 'Low'
```

Each factor is rated 1-5 by the user. The average gives the DREAD score. Risk level is auto-assigned.

---

### STRIDE METHODOLOGY

The app classifies threats into 6 STRIDE categories:
- **S**poofing — Impersonating someone/something
- **T**ampering — Modifying data or code
- **R**epudiation — Denying performed actions
- **I**nformation Disclosure — Exposing private data
- **D**enial of Service — Making system unavailable
- **E**levation of Privilege — Gaining unauthorized access

---

### DEPLOYMENT DETAILS

- **EC2 Instance:** t2.micro (free tier), Ubuntu 24.04
- **Docker:** App runs in container with Gunicorn (2 workers)
- **Nginx:** Reverse proxy handling HTTPS (Let's Encrypt cert)
- **Database:** SQLite currently, PostgreSQL-ready (psycopg2 + connection pooling configured)
- **Domain:** threat-toolkit.duckdns.org (free DuckDNS)
- **IP:** 52.72.57.162:5000 (direct), or via domain with HTTPS

---

### WHY THIS PROJECT MATTERS

This project demonstrates:
1. **Secure software development** — Not just building features, but building them securely
2. **Real-world deployment** — AWS EC2, Docker, Nginx, HTTPS, DNS — full production pipeline
3. **Team collaboration** — 4 developers working on separate modules with clean integration via Flask blueprints
4. **Security methodology knowledge** — STRIDE and DREAD are industry-standard threat modeling frameworks used by Microsoft, OWASP, and enterprise security teams
5. **Full-stack skills** — Backend (Python/Flask), Frontend (HTML/CSS/JS), Database (SQL), DevOps (Docker/AWS), Security (crypto, headers, auth)

---

### QUESTIONS YOU CAN NOW ANSWER ABOUT THIS PROJECT

- What does the app do? (Threat modeling with STRIDE/DREAD)
- How is security implemented? (13+ security controls listed above)
- What did each team member build? (See team roles table)
- How is it deployed? (AWS EC2 + Docker + Nginx + HTTPS)
- What's the tech stack? (Flask, SQLAlchemy, Gunicorn, PostgreSQL, Docker)
- How does DREAD scoring work? (Average of 5 factors, auto risk level)
- How does authentication work? (PBKDF2 hashing, rate limiting, session security)
- What makes it production-ready? (Gunicorn, non-root Docker, security headers, HSTS, SRI)

---

## PROMPT END
