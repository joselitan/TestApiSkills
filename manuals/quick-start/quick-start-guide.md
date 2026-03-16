# 🚀 QA Test Platform - Quick Start Guide

**Kom igång på 30 minuter**

---

## 📋 Innehållsförteckning

1. [Systemkrav](#systemkrav)
2. [Installation](#installation)
3. [Första körning](#första-körning)
4. [Kör dina första tester](#kör-dina-första-tester)
5. [Dashboard overview](#dashboard-overview)
6. [CI/CD setup](#cicd-setup)
7. [Nästa steg](#nästa-steg)

---

## 🖥️ Systemkrav

### Minimum Requirements
- **OS:** Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python:** 3.11 eller senare
- **RAM:** 4GB (8GB rekommenderat)
- **Disk:** 2GB ledigt utrymme
- **Internet:** Krävs för installation och CI/CD

### Verktyg som behövs
- **Git** - För versionshantering
- **Docker** (valfritt) - För containerized deployment
- **Web browser** - Chrome/Firefox/Edge för UI-tester

---

## 📦 Installation

### Steg 1: Klona Repository
```bash
git clone https://github.com/yourusername/qa-test-platform.git
cd qa-test-platform
```

### Steg 2: Skapa Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux  
python3 -m venv venv
source venv/bin/activate
```

### Steg 3: Installera Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Steg 4: Installera Playwright Browsers
```bash
playwright install chromium
```

### Steg 5: Verifiera Installation
```bash
python scripts/check_setup.py
```

**✅ Om allt är OK ser du:**
```
✓ Python version: 3.11.x
✓ All dependencies installed
✓ Database connection: OK
✓ Playwright browsers: OK
✓ Installation complete!
```

---

## 🎯 Första Körning

### Starta Applikationen
```bash
cd src
python app.py
```

**Du bör se:**
```
* Running on http://localhost:8080
* Debug mode: on
```

### Testa i Browser
1. Öppna: http://localhost:8080
2. Logga in med:
   - **Username:** admin
   - **Password:** password123

**✅ Success!** Du ser nu Guestbook-applikationen.

---

## 🧪 Kör Dina Första Tester

### API-tester (Rekommenderat att börja här)
```bash
# Starta appen i en terminal
cd src && python app.py

# Öppna ny terminal och kör tester
pytest tests/api/test_guestbook_api.py -v
```

**Förväntat resultat:**
```
tests/api/test_guestbook_api.py::test_login_success PASSED
tests/api/test_guestbook_api.py::test_create_entry PASSED
tests/api/test_guestbook_api.py::test_read_all_entries PASSED
...
========================= 8 passed in 12.34s =========================
```

### UI-tester
```bash
pytest tests/ui/test_guestbook_ui.py -v --browser chromium
```

### Säkerhetstester
```bash
pytest tests/security/test_security_headers.py -v
```

### Performance-tester
```bash
pytest tests/performance/test_load_testing.py -v
```

---

## 📊 Dashboard Overview

### Starta Dashboard
```bash
cd dashboard/backend
python app.py
```

Dashboard körs på: http://localhost:6001

### Dashboard Features
- **📈 Test Results** - Senaste test-körningar
- **⚡ Performance Metrics** - Response times, success rates
- **🏥 Health Status** - System health monitoring
- **📊 Trends** - Test trends över tid

### Populera Dashboard med Data
```bash
python scripts/populate_dashboard.py
```

---

## 🔄 CI/CD Setup

### GitHub Repository Setup

1. **Skapa GitHub Repository**
   ```bash
   git remote add origin https://github.com/yourusername/your-qa-project.git
   git push -u origin main
   ```

2. **Konfigurera GitHub Secrets**
   - Gå till: Settings → Secrets and variables → Actions
   - Lägg till secrets (om du har externa services)

3. **Aktivera GitHub Actions**
   - CI/CD pipeline startar automatiskt vid push
   - Se status under "Actions" tab

### Pipeline Stages
1. **🔍 Code Quality** - Black, flake8, pylint
2. **🧪 Unit Tests** - Grundläggande tester
3. **🔌 API Tests** - Integration tester
4. **🔒 Security Scan** - Säkerhetsanalys
5. **🖥️ UI Tests** - Browser automation
6. **⚡ Performance Tests** - Load testing
7. **🐳 Build** - Docker image
8. **🚀 Deploy** - Staging & Production

---

## 🎓 Nästa Steg

### För Studenter
1. **Läs Student Learning Manual** - Djupare förståelse
2. **Experimentera** - Ändra tester, lägg till nya
3. **Skapa egna tester** - Använd templates
4. **Utforska CI/CD** - Förstå pipeline

### För Instruktörer  
1. **Läs Instructor Guide** - Lektionsplaner och övningar
2. **Anpassa miljön** - Konfigurera för din kurs
3. **Använd Troubleshooting Guide** - Vanliga problem

### Avancerade Användare
1. **Technical Reference Manual** - Djup teknisk dokumentation
2. **Anpassa plattformen** - Lägg till egna features
3. **Integrera med andra verktyg** - Jenkins, SonarQube, etc.

---

## 🆘 Behöver Hjälp?

### Snabb Hjälp
- **Health Check:** http://localhost:8080/health
- **Logs:** Kolla `logs/app.log`
- **Database:** `data/guestbook.db`

### Vanliga Problem
- **Port redan används:** Ändra port i `src/app.py`
- **Database locked:** Stäng alla connections
- **Tests failar:** Kontrollera att appen körs

### Support
- **Troubleshooting Guide** - Detaljerade lösningar
- **GitHub Issues** - Rapportera bugs
- **Documentation** - Fullständig dokumentation

---

## ✅ Checklista - Du är redo när:

- [ ] Installation verifierad med `check_setup.py`
- [ ] Applikation startar på http://localhost:8080
- [ ] Kan logga in med admin/password123
- [ ] API-tester kör utan fel
- [ ] Dashboard visar data på http://localhost:6001
- [ ] GitHub Actions pipeline är grön
- [ ] Förstår grundläggande test-struktur

**🎉 Grattis! Du har nu en fullt fungerande QA Test Platform!**

---

*QA Test Platform v1.0 - Skapad för QA-studenter och professionella testare*