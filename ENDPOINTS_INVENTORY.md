# API Endpoints Inventory

Complete inventory of all API endpoints from `api/lib/Penhas/Routes.pm`. This document tracks test coverage status for the Perl → Python migration.

## Coverage Status

- ✅ Tested - Has Karate contract tests
- 🟡 Partial - Some scenarios tested, needs expansion
- ❌ Untested - No contract tests yet
- 🔒 Admin - Admin-only endpoints (lower priority)
- 🔧 Maintenance - Internal maintenance endpoints (excluded from migration)

## Public Endpoints

### Authentication

| Endpoint                      | Method | Auth | Status | Notes                       |
| ----------------------------- | ------ | ---- | ------ | --------------------------- |
| `/signup`                     | POST   | None | ✅      | Tested in `auth.feature`    |
| `/login`                      | POST   | None | ✅      | Tested in `auth.feature`    |
| `/logout`                     | POST   | JWT  | ✅      | Tested in `auth.feature`    |
| `/me`                         | GET    | JWT  | ✅      | Tested in `auth.feature`    |
| `/reset-password/request-new` | POST   | None | ❌      | Password reset request      |
| `/reset-password/write-new`   | POST   | None | ❌      | Password reset confirmation |

#### POST /signup

**Request Body:**
```json
{
  "dry": 0,                    // Required: 0 = create user, 1 = validate only
  "email": "user@example.com", // Required (if dry=0): Valid email with MX record
  "senha": "SecurePass123!",   // Required (if dry=0): Min 8 chars, must pass check_password_or_die
  "nome_completo": "Maria Silva", // Required: Min 5 chars, max 200
  "dt_nasc": "1990-01-15",     // Required: Date in YYYY-MM-DD format
  "cpf": "544.340.690-63",     // Required: Valid CPF, must match dt_nasc and nome_completo
  "cep": "01310100",           // Required: Valid CEP (8 digits)
  "genero": "Feminino",        // Required (if dry=0): Valid gender
  "apelido": "Maria",          // Required (if dry=0): Min 2 chars, max 40
  "raca": "Parda",            // Required (if dry=0): Valid race
  "nome_social": "",          // Optional: Required if genero is "trans" or "Outro"
  "app_version": "1.0.0"      // Required: Min 1 char, max 800
}
```

**Success Response (200):**
```json
{
  "session": "jwt_token_string",  // JWT token with {ses: session_id, typ: 'usr'}
  "_test_only_id": 123            // Only present when IS_TEST=1
}
```

**Error Responses:**
- **400 - Email already exists:**
  ```json
  {
    "error": "email_already_exists",
    "message": "E-mail já possui uma conta. Por favor, faça o o login, ou utilize a função \"Esqueci minha senha\".",
    "field": "email",
    "reason": "duplicate"
  }
  ```

- **400 - CPF already exists:**
  ```json
  {
    "error": "cpf_already_exists",
    "message": "Este CPF já possui uma conta. Entre em contato com o suporte caso não lembre do e-mail utilizado."
  }
  ```

- **400 - CPF validation failed:**
  ```json
  {
    "error": "cpf_not_match",
    "message": "Data de nascimento não confere com o CPF."
  }
  ```

- **400 - Name doesn't match CPF:**
  ```json
  {
    "error": "name_not_match",
    "message": "Nome deve ser escrito igual ao do seu CPF.",
    "field": "nome_completo",
    "reason": "invalid"
  }
  ```

- **400 - Invalid email:**
  ```json
  {
    "error": "invalid_email",
    "message": "Por favor, verificar validade do endereço de e-mail."
  }
  ```

- **429 - Too many CPF errors:**
  ```json
  {
    "error": "too_many_requests",
    "message": "Você fez muitos acessos recentemente. Aguarde e tente novamente.",
    "status": 429
  }
  ```

**Business Logic:**
- Validates CPF against external service (cpf_lookup)
- Validates email MX records
- Password must pass strength check (check_password_or_die)
- CPF is hashed with SHA256 before storage
- Password is hashed with SHA256 before storage
- Creates session in `clientes_active_sessions` table
- Logs login in `login_logs` table
- Rate limiting: 3 requests per minute per IP
- CPF error tracking: max 20 errors in 24h per IP

#### POST /login

**Request Body:**
```json
{
  "email": "user@example.com",  // Required: Valid email
  "senha": "password123",        // Required: Plain text password
  "app_version": "1.0.0"         // Required: Min 1 char, max 800
}
```

**Success Response (200):**
```json
{
  "session": "jwt_token_string",  // JWT token with {ses: session_id, typ: 'usr'}
  "_test_only_id": 123,          // Only present when IS_TEST=1
  "deleted_scheduled": 1         // Optional: Present if account was scheduled for deletion
}
```

**Error Responses:**
- **400 - User not found:**
  ```json
  {
    "error": "notfound",
    "message": "Você ainda não possui cadastro conosco.",
    "field": "email",
    "reason": "invalid"
  }
  ```

- **400 - Wrong password:**
  ```json
  {
    "error": "wrongpassword",
    "message": "Email ou senha inválidos",
    "field": "password",
    "reason": "invalid"
  }
  ```

- **400 - Account banned:**
  ```json
  {
    "error": "ban",
    "message": "A conta suspensa.",
    "field": "email",
    "reason": "invalid"
  }
  ```

- **400 - Password too weak:**
  ```json
  {
    "error": "wrongpassword_tooweak",
    "message": "Sua senha é fraca. Por favor, clique no botão \"Esqueci minha senha\" para resetar.",
    "field": "password",
    "reason": "invalid"
  }
  ```

**Business Logic:**
- Password compared as SHA256 hash
- Also checks MD5 hash for legacy compatibility
- Rate limiting: 3 requests per minute per IP
- Invalidates previous sessions if DELETE_PREVIOUS_SESSIONS env var is set
- Creates session in `clientes_active_sessions` table
- Logs login in `login_logs` table
- Sets Redis key `is_during_login:{user_id}` for 120 seconds

#### POST /logout

**Headers:**
- `x-api-key`: JWT token (required)

**Success Response (204):**
Empty body

**Error Responses:**
- **401 - Missing JWT:**
  ```json
  {
    "status": 401,
    "error": "missing_jwt",
    "message": "Not Authenticated"
  }
  ```

**Business Logic:**
- Deletes session from `clientes_active_sessions` table
- Removes session from Redis cache
- Session ID extracted from JWT token

#### GET /me

**Headers:**
- `x-api-key`: JWT token (required)

**Success Response (200):**
```json
{
  "user_profile": {
    "avatar_url": "https://...",
    "email": "user@example.com",
    "apelido": "Maria",
    "nome_completo": "Maria Silva",
    "genero": "Feminino",
    "dt_nasc": "1990-01-15",
    "cep": "01310100",
    "cpf_prefix": "5443",
    "raca": "Parda",
    "minibio": "",
    "nome_social": "",
    "skills": [1, 2, 3],
    "badges": [],
    "ja_foi_vitima_de_violencia": 0,
    "modo_camuflado_ativo": 0,
    "modo_anonimo_ativo": 0
  },
  "anonymous_avatar_url": "https://...",  // Only if modo_anonimo_ativo = 1
  "qtde_guardioes_ativos": 0,
  "modules": [
    {
      "code": "timeline",
      "meta": {}
    }
  ],
  "quiz_session": {}  // Only if user has incomplete quiz
}
```

**Error Responses:**
- **401 - Missing JWT:**
  ```json
  {
    "status": 401,
    "error": "missing_jwt",
    "message": "Not Authenticated"
  }
  ```

- **403 - Invalid/expired session:**
  ```json
  {
    "error": "jwt_logout",
    "message": "Está sessão não está mais válida (Usuário saiu)"
  }
  ```

- **404 - User not found:**
  ```json
  {
    "error": "user_not_found",
    "message": "User not found"
  }
  ```

**Business Logic:**
- Validates JWT token and extracts session ID
- Checks session exists in `clientes_active_sessions` table
- Caches user ID in Redis for 5 minutes
- Updates user activity timestamp
- Returns quiz session if incomplete
- Returns modules based on user access permissions
- Rate limiting: 120 requests per 60 seconds per user

### News & Media

| Endpoint         | Method | Auth | Status | Notes                  |
| ---------------- | ------ | ---- | ------ | ---------------------- |
| `/news-redirect` | GET    | None | ❌      | News redirect endpoint |
| `/get-proxy`     | GET    | None | ❌      | Media proxy endpoint   |

### Ponto de Apoio (Public)

| Endpoint                            | Method | Auth  | Status | Notes                           |
| ----------------------------------- | ------ | ----- | ------ | ------------------------------- |
| `/pontos-de-apoio-dados-auxiliares` | GET    | None  | ✅      | Tested in `ponto-apoio.feature` |
| `/pontos-de-apoio`                  | GET    | None  | ✅      | Tested in `ponto-apoio.feature` |
| `/pontos-de-apoio/:ponto_apoio_id`  | GET    | None  | ✅      | Tested in `ponto-apoio.feature` |
| `/ponto-apoio-unlimited`            | GET    | Token | ✅      | Tested in `ponto-apoio.feature` |
| `/geocode`                          | GET    | None  | ✅      | Tested in `ponto-apoio.feature` |

### Anonymous Questionnaire

| Endpoint                       | Method | Auth  | Status | Notes                    |
| ------------------------------ | ------ | ----- | ------ | ------------------------ |
| `/anon-questionnaires/config`  | GET    | Token | ❌      | Quiz configuration       |
| `/anon-questionnaires`         | GET    | Token | ❌      | List questionnaires      |
| `/anon-questionnaires/new`     | POST   | Token | ❌      | Create new questionnaire |
| `/anon-questionnaires/history` | GET    | Token | ❌      | Questionnaire history    |
| `/anon-questionnaires/process` | POST   | Token | ❌      | Process questionnaire    |

### Guardian Invitations

| Endpoint        | Method | Auth  | Status | Notes                    |
| --------------- | ------ | ----- | ------ | ------------------------ |
| `/web/guardiao` | GET    | Token | ❌      | Get guardian invitation  |
| `/web/guardiao` | POST   | Token | ❌      | Accept/reject invitation |

### Badge Acceptance

| Endpoint        | Method | Auth  | Status | Notes                 |
| --------------- | ------ | ----- | ------ | --------------------- |
| `/badge/accept` | GET    | Token | ❌      | Badge acceptance page |
| `/badge/accept` | POST   | Token | ❌      | Accept badge          |

### Web FAQ

| Endpoint                    | Method | Auth | Status | Notes                |
| --------------------------- | ------ | ---- | ------ | -------------------- |
| `/web/faq`                  | GET    | None | ❌      | FAQ index            |
| `/web/faq/_botao_contato_`  | GET    | None | ❌      | Contact button       |
| `/web/faq/conta-exclusao`   | GET    | None | ❌      | Account deletion FAQ |
| `/web/faq/:faq_id`          | GET    | None | ❌      | FAQ detail           |
| `/web/termos-de-uso`        | GET    | None | ❌      | Terms of service     |
| `/web/politica-privacidade` | GET    | None | ❌      | Privacy policy       |

## Authenticated Endpoints

### User Profile

| Endpoint                 | Method | Auth | Status | Notes                     |
| ------------------------ | ------ | ---- | ------ | ------------------------- |
| `/me`                    | GET    | JWT  | ✅      | Tested in `auth.feature`  |
| `/me`                    | PUT    | JWT  | ❌      | Update profile            |
| `/me`                    | DELETE | JWT  | ❌      | Delete account            |
| `/me/delete-text`        | GET    | JWT  | ❌      | Get deletion text         |
| `/me/unread-notif-count` | GET    | JWT  | ❌      | Unread notification count |
| `/me/notifications`      | GET    | JWT  | ❌      | List notifications        |
| `/me/preferences`        | GET    | JWT  | ❌      | Get preferences           |
| `/me/preferences`        | POST   | JWT  | ❌      | Update preferences        |

### User Actions

| Endpoint                                | Method | Auth | Status | Notes                    |
| --------------------------------------- | ------ | ---- | ------ | ------------------------ |
| `/logout`                               | POST   | JWT  | ✅      | Tested in `auth.feature` |
| `/reactivate`                           | POST   | JWT  | ❌      | Reactivate account       |
| `/report-profile`                       | POST   | JWT  | ❌      | Report user profile      |
| `/block-profile`                        | POST   | JWT  | ❌      | Block user profile       |
| `/me/call-police-pressed`               | POST   | JWT  | ❌      | Track police call        |
| `/me/inc-login-offline`                 | POST   | JWT  | ❌      | Track offline login      |
| `/me/modo-anonimo-toggle`               | POST   | JWT  | ❌      | Toggle anonymous mode    |
| `/me/modo-camuflado-toggle`             | POST   | JWT  | ❌      | Toggle camouflage mode   |
| `/me/ja-foi-vitima-de-violencia-toggle` | POST   | JWT  | ❌      | Toggle victim status     |

### Timeline

| Endpoint                      | Method | Auth | Status | Notes                        |
| ----------------------------- | ------ | ---- | ------ | ---------------------------- |
| `/timeline`                   | GET    | JWT  | ✅      | Tested in `timeline.feature` |
| `/timeline/:tweet_id/comment` | POST   | JWT  | ✅      | Tested in `timeline.feature` |
| `/timeline/:tweet_id/like`    | POST   | JWT  | ✅      | Tested in `timeline.feature` |
| `/timeline/:tweet_id/report`  | POST   | JWT  | ✅      | Tested in `timeline.feature` |

### Tweets

| Endpoint     | Method | Auth | Status | Notes                        |
| ------------ | ------ | ---- | ------ | ---------------------------- |
| `/me/tweets` | POST   | JWT  | ✅      | Tested in `timeline.feature` |
| `/me/tweets` | DELETE | JWT  | ❌      | Delete tweet                 |

### Quiz

| Endpoint   | Method | Auth | Status | Notes        |
| ---------- | ------ | ---- | ------ | ------------ |
| `/me/quiz` | POST   | JWT  | ❌      | Process quiz |

### Media

| Endpoint          | Method | Auth | Status | Notes          |
| ----------------- | ------ | ---- | ------ | -------------- |
| `/me/media`       | POST   | JWT  | ❌      | Upload media   |
| `/media-download` | GET    | JWT  | ❌      | Download media |

### Tasks (Tarefas)

| Endpoint            | Method | Auth | Status | Notes            |
| ------------------- | ------ | ---- | ------ | ---------------- |
| `/me/tarefas`       | GET    | JWT  | ❌      | List tasks       |
| `/me/tarefas/sync`  | POST   | JWT  | ❌      | Sync tasks       |
| `/me/tarefas/nova`  | POST   | JWT  | ❌      | Create task      |
| `/me/tarefas/batch` | POST   | JWT  | ❌      | Batch sync tasks |

### Guardians (Guardioes)

| Endpoint                  | Method | Auth | Status | Notes                  |
| ------------------------- | ------ | ---- | ------ | ---------------------- |
| `/me/guardioes`           | GET    | JWT  | ❌      | List guardians         |
| `/me/guardioes`           | POST   | JWT  | ❌      | Create/update guardian |
| `/me/guardioes/:guard_id` | PUT    | JWT  | ❌      | Update guardian        |
| `/me/guardioes/:guard_id` | DELETE | JWT  | ❌      | Delete guardian        |
| `/me/guardioes/alert`     | POST   | JWT  | ❌      | Alert guardians        |

### Audio Events

| Endpoint                              | Method | Auth | Status | Notes                  |
| ------------------------------------- | ------ | ---- | ------ | ---------------------- |
| `/me/audios`                          | POST   | JWT  | ❌      | Upload audio           |
| `/me/audios`                          | GET    | JWT  | ❌      | List audio events      |
| `/me/audios/:event_id`                | GET    | JWT  | ❌      | Get audio event detail |
| `/me/audios/:event_id`                | DELETE | JWT  | ❌      | Delete audio event     |
| `/me/audios/:event_id/download`       | GET    | JWT  | ❌      | Download audio         |
| `/me/audios/:event_id/request-access` | POST   | JWT  | ❌      | Request audio access   |

### Ponto de Apoio (User)

| Endpoint                               | Method | Auth | Status | Notes                           |
| -------------------------------------- | ------ | ---- | ------ | ------------------------------- |
| `/me/sugerir-pontos-de-apoio`          | POST   | JWT  | ✅      | Tested in `ponto-apoio.feature` |
| `/me/sugerir-pontos-de-apoio-completo` | POST   | JWT  | ✅      | Tested in `ponto-apoio.feature` |
| `/me/pontos-de-apoio`                  | GET    | JWT  | ✅      | Tested in `ponto-apoio.feature` |
| `/me/pontos-de-apoio/:ponto_apoio_id`  | GET    | JWT  | ✅      | Tested in `ponto-apoio.feature` |
| `/me/avaliar-pontos-de-apoio`          | POST   | JWT  | ✅      | Tested in `ponto-apoio.feature` |
| `/me/geocode`                          | GET    | JWT  | ❌      | User geocode endpoint           |

### Chat

| Endpoint             | Method | Auth | Status | Notes                |
| -------------------- | ------ | ---- | ------ | -------------------- |
| `/search-users`      | GET    | JWT  | ❌      | Search users         |
| `/profile`           | GET    | JWT  | ❌      | Get user profile     |
| `/me/chats`          | GET    | JWT  | ❌      | List chat sessions   |
| `/me/chats-session`  | POST   | JWT  | ❌      | Open chat session    |
| `/me/chats-session`  | DELETE | JWT  | ❌      | Delete chat session  |
| `/me/chats-messages` | POST   | JWT  | ❌      | Send message         |
| `/me/chats-messages` | GET    | JWT  | ❌      | List messages        |
| `/me/manage-blocks`  | POST   | JWT  | ❌      | Manage blocked users |

### Filters

| Endpoint         | Method | Auth | Status | Notes         |
| ---------------- | ------ | ---- | ------ | ------------- |
| `/filter-tags`   | GET    | JWT  | ❌      | Filter tags   |
| `/filter-skills` | GET    | JWT  | ❌      | Filter skills |

## Admin Endpoints

| Endpoint                               | Method | Auth  | Status | Notes                     |
| -------------------------------------- | ------ | ----- | ------ | ------------------------- |
| `/admin/login`                         | GET    | None  | 🔒      | Admin login page          |
| `/admin/login`                         | POST   | None  | 🔒      | Admin login               |
| `/admin/logout`                        | GET    | Admin | 🔒      | Admin logout              |
| `/admin`                               | GET    | Admin | 🔒      | Admin dashboard           |
| `/admin/users`                         | GET    | Admin | 🔒      | Search users              |
| `/admin/users-audio-status`            | GET    | Admin | 🔒      | User audio status         |
| `/admin/send-message`                  | POST   | Admin | 🔒      | Send message to user      |
| `/admin/user-messages`                 | GET    | Admin | 🔒      | List user messages        |
| `/admin/user-messages-delete`          | GET    | Admin | 🔒      | Delete message            |
| `/admin/notifications`                 | GET    | Admin | 🔒      | List notifications        |
| `/admin/add-notification`              | GET    | Admin | 🔒      | New notification template |
| `/admin/add-notification`              | POST   | Admin | 🔒      | Create notification       |
| `/admin/message-detail`                | GET    | Admin | 🔒      | Notification detail       |
| `/admin/bignum`                        | GET    | Admin | 🔒      | Big numbers dashboard     |
| `/admin/schedule-delete`               | POST   | Admin | 🔒      | Schedule user deletion    |
| `/admin/unschedule-delete`             | GET    | Admin | 🔒      | Unschedule deletion       |
| `/admin/ponto-apoio-sugg`              | GET    | Admin | 🔒      | List PA suggestions       |
| `/admin/analisar-sugestao-ponto-apoio` | GET    | Admin | 🔒      | Review PA suggestion      |
| `/admin/analisar-sugestao-ponto-apoio` | POST   | Admin | 🔒      | Process PA suggestion     |
| `/admin/badges`                        | GET    | Admin | 🔒      | Badge assignment form     |
| `/admin/badges/assign`                 | GET    | Admin | 🔒      | Badge assignment list     |
| `/admin/badges/assign`                 | POST   | Admin | 🔒      | Process badge assignment  |
| `/admin/badges/confirm`                | GET    | Admin | 🔒      | Confirm badge changes     |
| `/admin/badges/confirm`                | POST   | Admin | 🔒      | Confirm badge changes     |
| `/admin/badges/success`                | GET    | Admin | 🔒      | Badge success page        |

## Maintenance Endpoints

| Endpoint                            | Method | Auth   | Status | Notes                |
| ----------------------------------- | ------ | ------ | ------ | -------------------- |
| `/maintenance/tick-rss`             | GET    | Secret | 🔧      | RSS feed ticker      |
| `/maintenance/tags-clear-cache`     | GET    | Secret | 🔧      | Clear tags cache     |
| `/maintenance/reindex-all-news`     | GET    | Secret | 🔧      | Reindex news         |
| `/maintenance/housekeeping`         | GET    | Secret | 🔧      | Housekeeping tasks   |
| `/maintenance/tick-notifications`   | GET    | Secret | 🔧      | Notification ticker  |
| `/maintenance/fix_tweets_parent_id` | GET    | Secret | 🔧      | Fix tweet parent IDs |

## Test Coverage Summary

- **Total Endpoints**: ~80
- **Tested**: 15 (19%)
- **Partial**: 0 (0%)
- **Untested**: 50 (63%)
- **Admin**: 20 (25%) - Lower priority
- **Maintenance**: 6 (8%) - Excluded from migration

## Priority for Test Coverage

### Phase 1: Core User Features (Current)
- ✅ Authentication (signup, login, logout, /me)
- ✅ Timeline (list, create, comment, like, report)
- ✅ Ponto de Apoio (search, detail, suggest, rate)

### Phase 2: User Features (Next)
- Chat (sessions, messages, blocks)
- Quiz (process, history)
- Media (upload, download)
- Tasks (list, sync, create)
- Guardians (CRUD, alerts)
- Audio events (upload, list, download)
- Notifications (list, unread count)
- Preferences (get, update)

### Phase 3: Public Features
- Anonymous questionnaire
- Guardian invitations
- Badge acceptance
- Web FAQ
- Password reset

### Phase 4: Admin Features (Lower Priority)
- User management
- Notifications management
- Ponto de Apoio moderation
- Badge assignment

## Notes

- Admin endpoints are lower priority for migration
- Maintenance endpoints are excluded from migration
- Some endpoints may require special tokens or environment variables
- Test coverage will expand as migration progresses

