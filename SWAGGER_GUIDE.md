# 📚 Swagger API Documentation - Snabbguide

## Vad Har Implementerats?

✅ **Swagger/OpenAPI dokumentation** för alla API endpoints
✅ **Interaktiv API-testning** direkt i browsern
✅ **JWT Authentication** support i Swagger UI
✅ **Automatisk validering** av requests

## Hur Använder Du Det?

### 1. Starta Applikationen
```bash
python app.py
```

### 2. Öppna Swagger UI
Gå till: **http://localhost:8080/apidocs/**

### 3. Testa API:et

#### Steg 1: Logga In
1. Hitta **Authentication** sektionen
2. Klicka på **POST /api/login**
3. Klicka **"Try it out"**
4. Fyll i:
   ```json
   {
     "username": "admin",
     "password": "password123"
   }
   ```
5. Klicka **"Execute"**
6. Kopiera **token** från response

#### Steg 2: Auktorisera
1. Klicka på **"Authorize"** knappen (🔒 högst upp)
2. Skriv: `Bearer {din-token-här}`
3. Klicka **"Authorize"**
4. Klicka **"Close"**

#### Steg 3: Testa Endpoints
Nu kan du testa alla endpoints:
- **POST /api/guestbook** - Skapa entry
- **GET /api/guestbook** - Hämta alla entries
- **GET /api/guestbook/{id}** - Hämta en entry
- **PUT /api/guestbook/{id}** - Uppdatera entry
- **DELETE /api/guestbook/{id}** - Radera entry
- **DELETE /api/guestbook/bulk** - Radera flera
- **POST /api/guestbook/import** - Importera Excel

## Funktioner

### 📋 Komplett Dokumentation
- Alla endpoints dokumenterade
- Request/Response exempel
- Parametrar och datatyper
- Error responses

### 🧪 Interaktiv Testning
- "Try it out" för varje endpoint
- Fyll i formulär direkt i UI
- Se request och response live
- Kopiera curl-kommandon

### 🔐 JWT Authentication
- Inbyggd authorization
- Bearer token support
- Automatisk header-hantering

### ✅ Validering
- Schema validation
- Required fields markerade
- Datatyp-kontroll
- Exempel-värden

## API Översikt

### Authentication
- **POST /api/login** - Få JWT token

### Guestbook CRUD
- **POST /api/guestbook** - Skapa ny entry
- **GET /api/guestbook** - Lista entries (pagination + search)
- **GET /api/guestbook/{id}** - Hämta specifik entry
- **PUT /api/guestbook/{id}** - Uppdatera entry
- **DELETE /api/guestbook/{id}** - Radera entry

### Bulk Operations
- **DELETE /api/guestbook/bulk** - Radera flera entries

### Import
- **POST /api/guestbook/import** - Importera från Excel

## Tips & Tricks

### Exportera API Spec
Gå till: **http://localhost:8080/apispec.json**
- Få OpenAPI spec i JSON-format
- Kan användas för code generation
- Importera till Postman/Insomnia

### Curl Kommandon
Varje request visar curl-kommando:
```bash
curl -X POST "http://localhost:8080/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
```

### Code Generation
Använd OpenAPI spec för att generera:
- Client libraries (Python, JavaScript, Java, etc.)
- Server stubs
- Test cases

## Fördelar

✅ **Ingen Postman behövs** - Testa direkt i browsern
✅ **Alltid uppdaterad** - Dokumentation lever i koden
✅ **Lätt att dela** - Skicka bara en länk
✅ **Interaktiv** - Testa och se resultat direkt
✅ **Professionell** - Enterprise-grade dokumentation

## Nästa Steg

1. ✅ Swagger implementerat
2. ⏳ Testa alla endpoints via Swagger UI
3. ⏳ Dela API-dokumentationen med teamet
4. ⏳ Exportera OpenAPI spec för CI/CD
