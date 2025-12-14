# COMM-SERVICE Frontend Integration Guide

## Overview

The Communication Service provides REST APIs for messages, notifications, documents, and email queue management, plus real-time WebSocket updates.

**Base URL**: `http://localhost/comm`
**WebSocket URL**: `ws://localhost/ws/notifications/{user_id}/`
**API Documentation**: `http://localhost/comm/api/docs` (Swagger UI)

---

## Technology Stack

- **Django Ninja**: Modern FastAPI-style API framework
- **Django Channels**: WebSocket support for real-time updates
- **MinIO**: S3-compatible object storage for file uploads
- **Celery + Redis**: Async task queue (for future email processing)

---

## Authentication

Currently using **AllowAny** permissions for development. In production, add JWT/OAuth authentication headers:

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer YOUR_TOKEN_HERE'
};
```

---

## 1. Messages API

### 1.1 Create Message

Send a message from one user to another. **Automatically broadcasts to receiver via WebSocket**.

```javascript
// POST /comm/api/messages/
const createMessage = async (senderID, receiverID, subject, body) => {
  const response = await fetch('http://localhost/comm/api/messages/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender_id: senderID,
      receiver_id: receiverID,
      subject: subject,
      body: body,
      metadata: {}
    })
  });
  return await response.json();
};

// Example usage
const message = await createMessage(
  '123e4567-e89b-12d3-a456-426614174000',
  '987e6543-e21b-12d3-a456-426614174999',
  'Meeting Tomorrow',
  'Hey, are we still on for the meeting at 10am?'
);

console.log(message);
/* Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "123e4567-e89b-12d3-a456-426614174000",
  "receiver_id": "987e6543-e21b-12d3-a456-426614174999",
  "subject": "Meeting Tomorrow",
  "body": "Hey, are we still on for the meeting at 10am?",
  "created_at": "2025-01-15T10:30:00Z",
  "read_at": null,
  "metadata": {},
  "sender_data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user123e4567-e89b-12d3-a456-426614174000@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  },
  "receiver_data": { ... }
}
*/
```

### 1.2 Get Received Messages

```javascript
// GET /comm/api/messages/received/{receiver_id}/
const getReceivedMessages = async (userID) => {
  const response = await fetch(`http://localhost/comm/api/messages/received/${userID}/`);
  return await response.json();
};

const messages = await getReceivedMessages('987e6543-e21b-12d3-a456-426614174999');
```

### 1.3 Get Sent Messages

```javascript
// GET /comm/api/messages/sent/{sender_id}/
const getSentMessages = async (userID) => {
  const response = await fetch(`http://localhost/comm/api/messages/sent/${userID}/`);
  return await response.json();
};
```

### 1.4 Mark Message as Read

```javascript
// POST /comm/api/messages/{message_id}/mark_read/
const markAsRead = async (messageID) => {
  const response = await fetch(
    `http://localhost/comm/api/messages/${messageID}/mark_read/`,
    { method: 'POST' }
  );
  return await response.json();
};
```

### 1.5 Get Single Message

```javascript
// GET /comm/api/messages/{message_id}/
const getMessage = async (messageID) => {
  const response = await fetch(`http://localhost/comm/api/messages/${messageID}/`);
  return await response.json();
};
```

### 1.6 Delete Message

```javascript
// DELETE /comm/api/messages/{message_id}/
const deleteMessage = async (messageID) => {
  const response = await fetch(`http://localhost/comm/api/messages/${messageID}/`, {
    method: 'DELETE'
  });
  return await response.json();
};
// Response: { "success": true, "message": "Message deleted" }
```

---

## 2. Notifications API

### 2.1 Create Notification

Create a notification for a user. **Automatically broadcasts to user via WebSocket**.

```javascript
// POST /comm/api/notifications/
const createNotification = async (userID, type, title, content) => {
  const response = await fetch('http://localhost/comm/api/notifications/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userID,
      type: type,  // 'email', 'push', or 'system'
      title: title,
      content: content,
      metadata: {}
    })
  });
  return await response.json();
};

const notification = await createNotification(
  '987e6543-e21b-12d3-a456-426614174999',
  'system',
  'New Message',
  'You have a new message from John Doe'
);

/* Response:
{
  "id": "660e9500-f39c-52e5-b827-557766551111",
  "user_id": "987e6543-e21b-12d3-a456-426614174999",
  "type": "system",
  "title": "New Message",
  "content": "You have a new message from John Doe",
  "created_at": "2025-01-15T10:35:00Z",
  "sent_at": null,
  "status": "pending",
  "attempts": 0,
  "last_error": null,
  "metadata": {},
  "user_data": { ... }
}
*/
```

### 2.2 Get User Notifications

```javascript
// GET /comm/api/notifications/user/{user_id}/
const getUserNotifications = async (userID) => {
  const response = await fetch(`http://localhost/comm/api/notifications/user/${userID}/`);
  return await response.json();
};
```

### 2.3 Get Single Notification

```javascript
// GET /comm/api/notifications/{notification_id}/
const getNotification = async (notificationID) => {
  const response = await fetch(`http://localhost/comm/api/notifications/${notificationID}/`);
  return await response.json();
};
```

### 2.4 Delete Notification

```javascript
// DELETE /comm/api/notifications/{notification_id}/
const deleteNotification = async (notificationID) => {
  const response = await fetch(`http://localhost/comm/api/notifications/${notificationID}/`, {
    method: 'DELETE'
  });
  return await response.json();
};
```

---

## 3. Documents / File Upload API

### 3.1 Upload Document

Upload a file to MinIO storage. Returns presigned download URL (expires in 1 hour).

```javascript
// POST /comm/api/documents/upload/
const uploadDocument = async (file, studentID = null, ownerUserID = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (studentID) formData.append('student_id', studentID);
  if (ownerUserID) formData.append('owner_user_id', ownerUserID);

  const response = await fetch('http://localhost/comm/api/documents/upload/', {
    method: 'POST',
    body: formData
  });
  return await response.json();
};

// Example: Upload from file input
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const result = await uploadDocument(file, 'student-uuid-here');

console.log(result);
/* Response:
{
  "id": "770f0611-g40d-63f6-c938-668877662222",
  "storage_path": "documents/770f0611-g40d-63f6-c938-668877662222/report.pdf",
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size_bytes": 245678,
  "uploaded_at": "2025-01-15T11:00:00Z",
  "download_url": "http://minio:9000/medtrack-documents/documents/...?X-Amz-Algorithm=...",
  "expires_in": 3600
}
*/
```

### 3.2 Get Document Details

Returns document metadata with fresh download URL.

```javascript
// GET /comm/api/documents/{document_id}/
const getDocument = async (documentID) => {
  const response = await fetch(`http://localhost/comm/api/documents/${documentID}/`);
  return await response.json();
};

const doc = await getDocument('770f0611-g40d-63f6-c938-668877662222');
console.log(doc.download_url);  // Use this URL to download the file
```

### 3.3 Get Student Documents

```javascript
// GET /comm/api/documents/student/{student_id}/
const getStudentDocuments = async (studentID) => {
  const response = await fetch(`http://localhost/comm/api/documents/student/${studentID}/`);
  return await response.json();
};
```

### 3.4 Download Document

```javascript
const downloadDocument = async (documentID) => {
  // First, get the document to retrieve download URL
  const doc = await getDocument(documentID);

  // Open download URL in new tab or download programmatically
  window.open(doc.download_url, '_blank');
};
```

### 3.5 Delete Document

Deletes both the database record and the file from MinIO storage.

```javascript
// DELETE /comm/api/documents/{document_id}/
const deleteDocument = async (documentID) => {
  const response = await fetch(`http://localhost/comm/api/documents/${documentID}/`, {
    method: 'DELETE'
  });
  return await response.json();
};
```

---

## 4. Email Queue API

### 4.1 Add Email to Queue

```javascript
// POST /comm/api/email_queue/
const queueEmail = async (recipientEmail, subject, body) => {
  const response = await fetch('http://localhost/comm/api/email_queue/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recipient_email: recipientEmail,
      subject: subject,
      body: body,
      metadata: {}
    })
  });
  return await response.json();
};
```

### 4.2 Get Pending Emails

```javascript
// GET /comm/api/email_queue/pending/
const getPendingEmails = async () => {
  const response = await fetch('http://localhost/comm/api/email_queue/pending/');
  return await response.json();
};
```

---

## 5. WebSocket Real-Time Updates

### 5.1 Connect to WebSocket

Connect to receive real-time notifications and messages.

```javascript
// WebSocket URL: ws://localhost/ws/notifications/{user_id}/
const connectWebSocket = (userID) => {
  const ws = new WebSocket(`ws://localhost/ws/notifications/${userID}/`);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('WebSocket event received:', data);

    if (data.type === 'connection_established') {
      console.log('Connection confirmed:', data.message);
    }

    if (data.type === 'message_created') {
      // New message received
      console.log('New message:', data.data);
      // Update UI to show new message notification
      showMessageNotification(data.data);
    }

    if (data.type === 'notification_created') {
      // New notification received
      console.log('New notification:', data.data);
      // Update UI to show notification
      showNotification(data.data);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Optionally reconnect after delay
    setTimeout(() => connectWebSocket(userID), 5000);
  };

  return ws;
};

// Usage
const userID = '987e6543-e21b-12d3-a456-426614174999';
const socket = connectWebSocket(userID);
```

### 5.2 WebSocket Event Types

#### Connection Established
```json
{
  "type": "connection_established",
  "message": "Connected to notifications for user 987e6543-e21b-12d3-a456-426614174999"
}
```

#### Message Created
Triggered when a new message is sent TO this user.

```json
{
  "type": "message_created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sender_id": "123e4567-e89b-12d3-a456-426614174000",
    "receiver_id": "987e6543-e21b-12d3-a456-426614174999",
    "subject": "Meeting Tomorrow",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Notification Created
Triggered when a new notification is created FOR this user.

```json
{
  "type": "notification_created",
  "data": {
    "id": "660e9500-f39c-52e5-b827-557766551111",
    "user_id": "987e6543-e21b-12d3-a456-426614174999",
    "type": "system",
    "title": "New Message",
    "content": "You have a new message from John Doe",
    "created_at": "2025-01-15T10:35:00Z"
  }
}
```

---

## 6. Complete React Example

```javascript
import { useState, useEffect } from 'react';

const CommServiceDemo = () => {
  const [messages, setMessages] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [ws, setWs] = useState(null);
  const userID = '987e6543-e21b-12d3-a456-426614174999';

  // Connect WebSocket on mount
  useEffect(() => {
    const socket = new WebSocket(`ws://localhost/ws/notifications/${userID}/`);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'message_created') {
        // New message - fetch latest messages
        fetchMessages();
        alert(`New message: ${data.data.subject}`);
      }

      if (data.type === 'notification_created') {
        // New notification - add to list
        setNotifications(prev => [data.data, ...prev]);
        alert(`New notification: ${data.data.title}`);
      }
    };

    setWs(socket);

    return () => socket.close();
  }, [userID]);

  // Fetch messages
  const fetchMessages = async () => {
    const response = await fetch(`http://localhost/comm/api/messages/received/${userID}/`);
    const data = await response.json();
    setMessages(data);
  };

  // Send message
  const sendMessage = async (receiverID, subject, body) => {
    const response = await fetch('http://localhost/comm/api/messages/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender_id: userID,
        receiver_id: receiverID,
        subject,
        body,
        metadata: {}
      })
    });
    const newMessage = await response.json();
    console.log('Message sent:', newMessage);
  };

  // Upload document
  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('owner_user_id', userID);

    const response = await fetch('http://localhost/comm/api/documents/upload/', {
      method: 'POST',
      body: formData
    });
    const result = await response.json();
    console.log('File uploaded:', result);
    alert(`File uploaded! Download URL: ${result.download_url}`);
  };

  return (
    <div>
      <h1>COMM-SERVICE Demo</h1>

      <section>
        <h2>Messages ({messages.length})</h2>
        <button onClick={fetchMessages}>Refresh Messages</button>
        {messages.map(msg => (
          <div key={msg.id}>
            <strong>{msg.subject}</strong> from {msg.sender_data?.first_name}
            <p>{msg.body}</p>
          </div>
        ))}
      </section>

      <section>
        <h2>Send Message</h2>
        <button onClick={() => sendMessage(
          '123e4567-e89b-12d3-a456-426614174000',
          'Test',
          'Hello World'
        )}>
          Send Test Message
        </button>
      </section>

      <section>
        <h2>Upload File</h2>
        <input type="file" onChange={(e) => uploadFile(e.target.files[0])} />
      </section>

      <section>
        <h2>Notifications ({notifications.length})</h2>
        {notifications.map(notif => (
          <div key={notif.id}>
            <strong>{notif.title}</strong>
            <p>{notif.content}</p>
          </div>
        ))}
      </section>
    </div>
  );
};

export default CommServiceDemo;
```

---

## 7. Testing Endpoints

### Using cURL

```bash
# Create message
curl -X POST http://localhost/comm/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "123e4567-e89b-12d3-a456-426614174000",
    "receiver_id": "987e6543-e21b-12d3-a456-426614174999",
    "subject": "Test Message",
    "body": "Hello from cURL"
  }'

# Get received messages
curl http://localhost/comm/api/messages/received/987e6543-e21b-12d3-a456-426614174999/

# Upload file
curl -X POST http://localhost/comm/api/documents/upload/ \
  -F "file=@/path/to/document.pdf" \
  -F "student_id=student-uuid"

# Test WebSocket with wscat
npm install -g wscat
wscat -c "ws://localhost/ws/notifications/987e6543-e21b-12d3-a456-426614174999/"
```

---

## 8. API Documentation (Swagger)

Visit **http://localhost/comm/api/docs** for interactive API documentation where you can:
- Browse all endpoints
- See request/response schemas
- Test endpoints directly from browser

---

## 9. Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Success
- **201 Created**: Resource created
- **400 Bad Request**: Invalid input
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Example error response:
```json
{
  "error": "Failed to upload file to storage"
}
```

---

## 10. Best Practices

1. **WebSocket Reconnection**: Implement reconnection logic with exponential backoff
2. **Download URLs**: Presigned URLs expire in 1 hour - refresh by calling GET document endpoint
3. **File Uploads**: Validate file size/type on frontend before uploading
4. **Real-time Updates**: Always connect WebSocket when user logs in for instant notifications
5. **Polling Fallback**: If WebSocket fails, poll `/api/messages/received/` and `/api/notifications/user/` periodically

---

## Summary

**COMM-SERVICE provides:**
- ✅ RESTful APIs for Messages, Notifications, Documents, Email Queue
- ✅ Real-time WebSocket updates for messages and notifications
- ✅ MinIO file storage with presigned download URLs
- ✅ Enriched responses with data from other microservices (AUTH, PROFILE, CORE)
- ✅ Automatic Swagger documentation at `/api/docs`

All endpoints maintain backward compatibility while using modern Django Ninja + Channels stack.
