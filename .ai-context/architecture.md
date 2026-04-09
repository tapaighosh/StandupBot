# StandupBot — System Architecture

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Team : "owns"
    Team ||--o{ Member : "has"
    Team ||--o{ Question : "has"
    Team ||--o{ Digest : "receives"
    Team ||--o{ TeamSettings : "has"
    Member ||--o{ Submission : "submits"
    Member ||--o{ StandupToken : "assigned"
    Digest ||--o{ DigestEntry : "contains"
    Submission ||--o{ Answer : "contains"
    User ||--o{ Subscription : "has"

    User {
        uuid id PK
        string email UK
        string name
        string google_id UK
        string avatar_url
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Team {
        uuid id PK
        uuid owner_id FK
        string name
        string timezone
        time reminder_time
        time digest_time
        time submission_window_start
        time submission_window_end
        boolean allow_late_submissions
        string slack_channel_id
        string slack_webhook_url
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Member {
        uuid id PK
        uuid team_id FK
        string email
        string name
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Question {
        uuid id PK
        uuid team_id FK
        string text
        int order_index
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    StandupToken {
        uuid id PK
        uuid member_id FK
        uuid team_id FK
        date standup_date
        string token_hash UK
        timestamp expires_at
        boolean is_used
        timestamp used_at
        timestamp created_at
    }

    Submission {
        uuid id PK
        uuid member_id FK
        uuid team_id FK
        date standup_date
        boolean is_late
        jsonb metadata
        timestamp submitted_at
        timestamp created_at
        timestamp updated_at
    }

    Answer {
        uuid id PK
        uuid submission_id FK
        uuid question_id FK
        text answer_text
        timestamp created_at
    }

    Digest {
        uuid id PK
        uuid team_id FK
        date digest_date
        text ai_summary
        text raw_content
        int total_members
        int responded_count
        jsonb non_responders
        jsonb blockers
        string status
        timestamp sent_at
        timestamp created_at
    }

    DigestEntry {
        uuid id PK
        uuid digest_id FK
        uuid member_id FK
        uuid submission_id FK
        boolean has_blocker
        timestamp created_at
    }

    TeamSettings {
        uuid id PK
        uuid team_id FK
        boolean email_reminders_enabled
        boolean slack_reminders_enabled
        boolean nudge_enabled
        int nudge_delay_minutes
        float low_response_alert_threshold
        timestamp created_at
        timestamp updated_at
    }

    Subscription {
        uuid id PK
        uuid user_id FK
        string stripe_customer_id
        string stripe_subscription_id
        string plan
        string status
        timestamp current_period_start
        timestamp current_period_end
        timestamp created_at
        timestamp updated_at
    }
```

---

## API Route Map

### Auth (`/api/v1/auth`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/signup` | Register via email |
| POST | `/login/google` | Google OAuth login |
| POST | `/refresh` | Refresh JWT token |
| POST | `/logout` | Invalidate session |
| GET | `/me` | Get current user profile |

### Teams (`/api/v1/teams`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create a new team |
| GET | `/` | List user's teams |
| GET | `/{team_id}` | Get team details |
| PUT | `/{team_id}` | Update team settings |
| DELETE | `/{team_id}` | Delete (soft) a team |
| POST | `/{team_id}/members` | Invite a member |
| GET | `/{team_id}/members` | List team members |
| DELETE | `/{team_id}/members/{member_id}` | Remove a member |
| PUT | `/{team_id}/questions` | Update team questions |
| GET | `/{team_id}/questions` | Get team questions |

### Submissions (`/api/v1/submissions`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/form/{token}` | Validate token & get form questions |
| POST | `/form/{token}` | Submit standup answers |

### Digests (`/api/v1/digests`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/{team_id}/today` | Get today's digest |
| GET | `/{team_id}/history` | Get digest history (paginated) |
| GET | `/{team_id}/{digest_id}` | Get specific digest |
| POST | `/{team_id}/trigger` | Manually trigger digest generation |

### Dashboard (`/api/v1/dashboard`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/{team_id}/stats` | Response rates, participation metrics |
| GET | `/{team_id}/blockers` | Blocker frequency trends |
| GET | `/{team_id}/members/{member_id}/stats` | Per-member stats |
| GET | `/{team_id}/export` | Export digest as PDF/CSV |

### Health (`/api/v1/health`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/ready` | Readiness probe (DB connection) |

---

## Service Layer Architecture

```mermaid
graph TB
    subgraph "API Layer"
        A[Auth Routes]
        B[Team Routes]
        C[Submission Routes]
        D[Digest Routes]
        E[Dashboard Routes]
    end

    subgraph "Service Layer"
        S1[AuthService]
        S2[TeamService]
        S3[TokenService]
        S4[SubmissionService]
        S5[DigestService]
        S6[NotificationService]
        S7[LLMService]
        S8[EmailService]
        S9[SlackService]
        S10[BillingService]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        M[SQLAlchemy Models]
    end

    subgraph "External Services"
        G[Google OAuth]
        O[OpenAI / Anthropic]
        R[Resend / Postmark]
        SL[Slack API]
        ST[Stripe]
    end

    subgraph "Background Jobs"
        J1[DigestJob]
        J2[ReminderJob]
        J3[NudgeJob]
    end

    A --> S1
    B --> S2
    C --> S3 & S4
    D --> S5
    E --> S5 & S4

    S1 --> G
    S5 --> S7 --> O
    S5 --> S8 --> R
    S5 --> S9 --> SL
    S6 --> S8 & S9
    S10 --> ST

    J1 --> S5
    J2 --> S6
    J3 --> S6

    S1 & S2 & S3 & S4 & S5 --> M --> DB
```

---

## Data Flow — Daily Digest Generation

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant DJ as DigestJob
    participant DB as PostgreSQL
    participant LLM as OpenAI/Anthropic
    participant Email as Resend
    participant Slack as Slack API

    Scheduler->>DJ: Trigger at configured digest_time
    DJ->>DB: Fetch team config + members
    DJ->>DB: Fetch today's submissions
    DJ->>DJ: Identify non-responders
    DJ->>DJ: Extract blocker keywords
    DJ->>LLM: Send submissions for summary
    alt LLM Success
        LLM-->>DJ: Return AI summary
    else LLM Failure
        DJ->>DJ: Continue without summary
    end
    DJ->>DJ: Assemble digest object
    DJ->>DB: Save digest record
    DJ->>Email: Send digest email to manager
    DJ->>Slack: Post to Slack channel (if connected)
    DJ->>DB: Log success/failure
```

---

## Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Generated: ReminderJob creates daily token
    Generated --> Validated: Member clicks link
    Validated --> Active: Token is valid & within window
    Active --> Used: Member submits standup
    Used --> [*]: Token marked as used

    Generated --> Expired: Window closes
    Validated --> Expired: Token past expiry
    Expired --> [*]: Rejected on form load

    Active --> Overwritten: Re-submission (if allowed)
    Overwritten --> Used: New submission stored
```

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/standupbot

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email
RESEND_API_KEY=your-resend-key
FROM_EMAIL=standups@yourdomain.com

# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# LLM
LLM_PROVIDER=openai  # or "anthropic"
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# App
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```
