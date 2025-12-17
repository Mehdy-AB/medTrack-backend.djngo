# Quick Start Testing Guide - Events & Consul

## Step 1: Create User Account

```http
POST http://localhost/auth/register
Content-Type: application/json

{
  "email": "encadrant@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "encadrant"
}
```

---

## Step 2: Login

```http
POST http://localhost/auth/login
Content-Type: application/json

{
  "email": "encadrant@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJhbGc...",  ← COPY THIS TOKEN!
  "refresh": "..."
}
```

---

## Step 3: Create Offer (Triggers RabbitMQ Events)

```http
POST http://localhost/core/offers
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "title": "Cardiology Internship",
  "description": "6-month internship",
  "service_id": "7aff8f27-69de-475f-bc2f-c7afee9a006e",
  "establishment_id": "728b74c2-902a-408c-9e85-057fe5395e71",
  "period_start": "2025-06-01",
  "period_end": "2025-08-31",
  "available_slots": 3
}
```

**Response:**
```json
{
  "id": "fe858040-f228-4289-b804-79cf0d467b8e",  ← SAVE THIS OFFER ID!
  "id": "9c25171e-1288-4a95-82f3-992b65fa55c5"
  "title": "Cardiology Internship",
  ...
}
```

---

## Step 4: Verify RabbitMQ Events

Check consumer logs to see events were processed:

```bash
# Profile consumer (indexes the offer)
docker-compose logs profile-service-consumer --tail=20

# Comm consumer (sends notifications)
docker-compose logs comm-service-consumer --tail=20
```

**Look for:**
```
📨 Received: core.offer.created
📇 Indexing offer: Cardiology Internship
✅ Message processed successfully
```

---

## Step 5: Get Offer (Tests Consul Service Discovery)

```http
GET http://localhost/core/offers/YOUR_OFFER_ID
Authorization: Bearer YOUR_TOKEN_HERE
```

**Response includes data from OTHER services via Consul:**
```json
{
  "id": "abc-123-def",
  "title": "Cardiology Internship",
  
  "service": {                           ← FROM profile-service
    "id": "...",
    "name": "Cardiology Department",
    "establishment": {                   ← FROM profile-service
      "id": "...",
      "name": "Central Hospital",
      "city": "Casablanca"
    }
  },
  
  "created_by_encadrant": {              ← FROM auth-service
    "id": "...",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**✅ If you see `service`, `establishment`, and `created_by_encadrant` with real data → Consul is working!**

---

## Step 6: Publish Offer (Another Event)

```http
PATCH http://localhost/core/offers/YOUR_OFFER_ID
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "status": "published"
}
```

Check consumer logs again:
```bash
docker-compose logs comm-service-consumer --tail=20
```

**Look for:**
```
📨 Received: core.offer.published
📢 Broadcasting: New offer published
```

---

## Quick Verification

### Check Consul UI
Open: http://localhost:8500

Should see all services as **"passing"** (green):
- auth-service
- profile-service
- core-service
- eval-service
- comm-service

### Check RabbitMQ UI
Open: http://localhost:15672 (admin/password)

Go to **Queues** tab:
- `profile.offers` - should show messages processed
- `comm.notifications` - should show messages processed

---

## Troubleshooting

**"Service data is NULL"**
→ The service_id/establishment_id doesn't exist. Check profile-service database:
```bash
docker-compose exec postgres psql -U postgres -d profile_db -c "SELECT id, name FROM profiles.services LIMIT 5;"
```

**"No events in consumer logs"**
→ Check consumers are running:
```bash
docker-compose ps | grep consumer
```

**"Could not discover service"**
→ Service not registered in Consul. Check service logs:
```bash
docker-compose logs core-service | grep Consul
```

---

## Summary

✅ **User created** → Can authenticate  
✅ **Offer created** → RabbitMQ event `core.offer.created` fires  
✅ **Consumers process** → See logs show event received  
✅ **Offer retrieved** → Data from profile-service & auth-service via Consul  
✅ **Offer published** → RabbitMQ event `core.offer.published` fires  

**All working = Events + Consul verified!** 🎉
