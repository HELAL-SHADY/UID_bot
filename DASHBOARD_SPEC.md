# Premium Admin Dashboard Design for Bybit UID Verification & Binance Payouts

## Project Vision
A luxury fintech admin dashboard for managing Bybit UID verification, Binance reward payouts, and Telegram user workflows. The dashboard is dark-first, responsive, and designed to support enterprise-grade security, live monitoring, and fast admin decisions.

## Architecture Overview

### Frontend
- Next.js 14+ with App Router
- TypeScript
- Tailwind CSS
- ShadCN UI components
- Framer Motion for motion and transitions
- Recharts for charts
- SWR / React Query for data fetching
- Optional: `next-auth` or custom JWT session middleware

### Backend
- Node.js + Express
- PostgreSQL database managed by Prisma ORM
- Redis for caching, rate limiting, session store
- WebSocket server for real-time updates (Socket.io or ws)
- REST API with GraphQL optional later
- Optional BFF pattern for dashboard-specific API

### Integrations
- Telegram Bot API for incoming user submissions and outbound messages
- Bybit API for UID verification and transaction validation
- Binance API for reward payouts and wallet balance
- Webhooks for status changes and payment notifications

## Folder Layout

```
/dashboard
  /app
    /admin
      /dashboard
      /uid-management
      /users
      /payouts
      /analytics
      /settings
      /notifications
  /components
  /lib
  /hooks
  /styles
  /types
/api
  /auth
  /users
  /submissions
  /reviews
  /payouts
  /notifications
  /settings
/backend
  /services
  /workers
  /websocket
  /integrations
/prisma
  schema.prisma
```

## UI/UX Page Structure

### 1. Overview Page

Primary dashboard with:
- Stat cards: Total Submitted UIDs, Pending Reviews, Approved UIDs, Rejected UIDs, Total Rewards Paid, Binance Wallet Balance, Today’s Submissions, Today’s Payments
- Activity timeline with admin actions and webhook events
- Recent Submissions table
- Recent Payouts table
- Performance charts: daily submissions, approval rate, payout volume
- System status indicators: telegram bot status, Binance API health, database status, webhook queue

### 2. UID Management Page

Key features:
- High-performance advanced table
- Columns: User ID, Telegram Username, Bybit UID, Submission Date, Verification Status, Reward Amount, Admin Notes, Actions
- Table controls: search, status filter, date range, sort
- Bulk actions: approve, reject, manual review
- Row actions: view details, approve, reject, add note, message user

### 3. UID Review Modal

Modal content:
- User snapshot: username, Telegram ID, registration date, join source
- Submission details: Bybit UID, submitted date, submission platform
- Verification result: verified, suspected duplicate, invalid format
- Historical context: previous submissions, previous reward history, past admin notes
- Internal notes editor
- Action buttons: Approve UID, Reject UID, Request Manual Review, Send Message to User

### 4. Binance Payout Center

Dashboard for payouts:
- Overview cards: pending, completed, failed, queued amount, available balance
- Pending payout queue table
- Completed payouts table
- Failed payouts table
- Transaction history table with filters and export
- Manual payout workflow: select submission -> confirm payout -> track status
- Auto-payout toggle and retry options

### 5. User Management

User admin console:
- Columns: Telegram ID, Username, Total Submissions, Total Approved, Total Rejected, Total Rewards Received, Registration Date, Status
- Actions: view profile, suspend/reactivate, add admin note, initiate message
- User profile detail panel with wallet summary, submission timeline, activity logs

### 6. Analytics Dashboard

Detailed charts and KPI sets:
- Daily UID submissions
- Approval and rejection rates
- Payment volume and payout velocity
- User growth and active users
- Revenue / expense trends (reward outflow)
- Custom date filtering: Today, 7d, 30d, custom range

### 7. Notifications

Real-time notification center with badge count:
- New UID submitted
- UID approved/rejected
- Payment completed
- Payment failed
- System health alerts
- Quick action buttons for common workflows

### 8. Settings Page

Admin configuration:
- Reward amount settings
- Binance API keys and wallet configuration
- Telegram bot token and webhook settings
- Verification rules and UID validation patterns
- Notification channels and preferences
- Admin roles and security controls
- Audit log access and session management

## Component Hierarchy

### Top-level shell
- `DashboardShell`
- `AdminSidebar`
- `TopNavBar`
- `PageHeader`
- `ContentGrid`

### Core UI components
- `StatCard`
- `StatusBadge`
- `DataTable`
- `TableRow`
- `FilterBar`
- `SearchInput`
- `DateRangePicker`
- `DropdownMenu`
- `ActionMenuButton`
- `GlassPanel`
- `SkeletonCard`
- `EmptyStatePanel`
- `ErrorBoundaryFallback`
- `ModalSheet`
- `SlideOverPanel`
- `ToastNotification`

### Dashboard-specific
- `OverviewStatsGrid`
- `ActivityTimeline`
- `RecentSubmissionsTable`
- `RecentPayoutsTable`
- `PerformanceChartCard`
- `WalletHealthCard`
- `SystemStatusPill`

### UID management
- `UidManagementTable`
- `UidReviewModal`
- `UidDetailsCard`
- `VerificationStatusBadge`
- `AdminNotesEditor`
- `BulkActionsBar`

### Payout center
- `PayoutOverviewCards`
- `PendingPayoutsTable`
- `PayoutHistoryTable`
- `PayoutActionButton`
- `ExportTransactionsButton`

### Users
- `UserTable`
- `UserProfilePanel`
- `UserActivityTimeline`
- `UserStatusBadge`

### Analytics
- `LineChartCard`
- `BarChartCard`
- `PieChartCard`
- `MetricTrendList`
- `DateFilterPills`

### Settings & security
- `SettingsSection`
- `ApiKeyPicker`
- `TwoFactorCard`
- `AccessControlForm`
- `AuditLogTable`

## Design System & Visual Style

### Color usage
- Base background: `#0B0B0B`
- Surface panels: `#161616`
- Text: `#FFFFFF`
- Secondary text: `#9CA3AF`
- Accent gold: `#FFB703`
- Success: `#10B981`
- Warning: `#F59E0B`
- Danger: `#EF4444`
- Borders: `#262626`

### Visual language
- Glassmorphism cards and soft blur surfaces
- Subtle gold gradients on CTAs and key badges
- Rounded corners with premium spacing
- Smooth navigation transitions and hover animations
- Minimal, elegant typography with strong contrast
- Dark neon-like highlights for active state and selected items

### Layout behavior
- Desktop: 3-column dashboard grid with dense panels
- Tablet: 2-column responsive layout
- Mobile: stacked cards, collapsible sidebar, bottom navigation actions
- Always maintain accessible font sizes and 24px touch targets for buttons

## Database Schema Suggestions

### Tables

#### `admins`
- `id` UUID PK
- `email` VARCHAR unique
- `name` VARCHAR
- `password_hash` TEXT
- `role` ENUM(`super_admin`, `admin`, `reviewer`)
- `two_factor_enabled` BOOLEAN
- `two_factor_secret` TEXT
- `status` ENUM(`active`, `suspended`, `pending`)
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

#### `users`
- `id` UUID PK
- `telegram_id` BIGINT unique
- `username` VARCHAR
- `first_name` VARCHAR
- `last_name` VARCHAR
- `status` ENUM(`active`, `suspended`, `blocked`)
- `created_at` TIMESTAMP
- `last_seen_at` TIMESTAMP

#### `uid_submissions`
- `id` UUID PK
- `user_id` FK -> users.id
- `telegram_username` VARCHAR
- `bybit_uid` VARCHAR
- `status` ENUM(`pending`, `approved`, `rejected`, `manual_review`)
- `reward_amount` DECIMAL(10,2)
- `verification_result` JSONB
- `submitted_at` TIMESTAMP
- `reviewed_at` TIMESTAMP nullable
- `reviewed_by` FK -> admins.id nullable
- `notes` TEXT
- `metadata` JSONB

#### `uid_reviews`
- `id` UUID PK
- `submission_id` FK -> uid_submissions.id
- `admin_id` FK -> admins.id
- `action` ENUM(`approve`, `reject`, `manual_review`, `note`)
- `comment` TEXT
- `created_at` TIMESTAMP

#### `payouts`
- `id` UUID PK
- `submission_id` FK -> uid_submissions.id nullable
- `user_id` FK -> users.id
- `amount` DECIMAL(12,2)
- `currency` VARCHAR
- `recipient_wallet` VARCHAR
- `status` ENUM(`queued`, `pending`, `completed`, `failed`, `cancelled`)
- `binance_transaction_id` VARCHAR nullable
- `error_code` VARCHAR nullable
- `error_message` TEXT nullable
- `created_at` TIMESTAMP
- `completed_at` TIMESTAMP nullable
- `processed_by` FK -> admins.id nullable

#### `transactions`
- `id` UUID PK
- `payout_id` FK -> payouts.id
- `type` ENUM(`withdrawal`, `reward`, `fee`, `adjustment`)
- `amount` DECIMAL(12,2)
- `currency` VARCHAR
- `status` ENUM(`success`, `pending`, `failed`)
- `reference` VARCHAR
- `created_at` TIMESTAMP
- `metadata` JSONB

#### `notifications`
- `id` UUID PK
- `type` VARCHAR
- `entity_id` UUID nullable
- `message` TEXT
- `level` ENUM(`info`, `success`, `warning`, `danger`)
- `read` BOOLEAN
- `created_at` TIMESTAMP

#### `audit_logs`
- `id` UUID PK
- `actor_type` ENUM(`admin`, `system`)
- `actor_id` UUID nullable
- `action` VARCHAR
- `entity_type` VARCHAR
- `entity_id` UUID nullable
- `details` JSONB
- `ip_address` VARCHAR nullable
- `user_agent` TEXT nullable
- `created_at` TIMESTAMP

#### `settings`
- `id` UUID PK
- `key` VARCHAR unique
- `value` JSONB
- `updated_at` TIMESTAMP

#### `api_keys`
- `id` UUID PK
- `label` VARCHAR
- `key_hash` TEXT
- `permissions` JSONB
- `active` BOOLEAN
- `created_at` TIMESTAMP
- `last_used_at` TIMESTAMP nullable

## API Architecture

### Auth
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `POST /api/auth/2fa/verify`
- `GET /api/auth/me`

### UID Submissions
- `GET /api/submissions`
- `GET /api/submissions/:id`
- `POST /api/submissions/:id/review`
- `POST /api/submissions/:id/note`
- `POST /api/submissions/bulk-review`
- `GET /api/submissions/stats`

### Payouts
- `GET /api/payouts`
- `GET /api/payouts/:id`
- `POST /api/payouts/manual`
- `POST /api/payouts/:id/retry`
- `POST /api/payouts/:id/cancel`
- `GET /api/payouts/stats`
- `GET /api/payouts/export`

### Users
- `GET /api/users`
- `GET /api/users/:id`
- `POST /api/users/:id/suspend`
- `POST /api/users/:id/reactivate`
- `POST /api/users/:id/notes`

### Analytics
- `GET /api/analytics/submissions`
- `GET /api/analytics/reviews`
- `GET /api/analytics/payments`
- `GET /api/analytics/users`

### Notifications
- `GET /api/notifications`
- `POST /api/notifications/:id/read`
- `POST /api/notifications/mark-all-read`

### Settings
- `GET /api/settings`
- `PATCH /api/settings`
- `GET /api/settings/security`
- `PATCH /api/settings/security`

### System / Health
- `GET /api/health`
- `GET /api/system/status`
- `GET /api/system/logs`

### WebSocket Events
- `submission.created`
- `submission.updated`
- `payout.updated`
- `notification.created`
- `system.alert`

## Real-Time Update Strategy
- Use WebSocket channel for live dashboard updates.
- Fall back to short-polling for stale clients.
- Push notification events for new UID submissions, payout status changes, admin alerts.
- Use Redis pub/sub to broadcast events between API workers and WebSocket server.

## Security and Access Control
- Role-based access control with explicit permissions
- Strong admin authentication and session management
- Optional OTP/2FA for admin sign-in
- Audit logs for every review, payout, and setting change
- API key management with scoped permissions
- Rate limiting on all sensitive routes
- Strict CORS and security headers
- Password hashing with bcrypt/argon2
- Input sanitization and server-side validation

## Performance & Production Readiness
- Use PostgreSQL connection pooling and Redis cache
- Index queries on `telegram_id`, `bybit_uid`, `status`, `created_at`
- Paginate all tables with cursor-based pagination
- Use incremental static regeneration for stable dashboard sections if applicable
- Lazy-load heavy chart components and tables
- Set up application monitoring and logging
- Add error boundaries and user-friendly failure states
- Export CSV/Excel from backend with streaming responses
- Use HTTPS and secure cookie / same-site settings

## Implementation Notes
- Build the dashboard as a separate `dashboard/` app that consumes the same backend API used by the bot.
- Keep Telegram bot and dashboard decoupled: the bot writes to the shared database or backend service, the dashboard reads and acts through secured APIs.
- Use `Framer Motion` for subtle entrance animations, hover transitions, and skeleton loading effects.
- Use `GlassPanel` patterns for the data cards and tables to preserve premium feel.
- Use a dark theme by default and provide a `light` mode toggle for accessibility.
- Use `Recharts` for polished, interactive charts and `ShadCN UI` for consistent form controls.

## Recommended Next Step
Create a new dashboard workspace under `dashboard/` with:
- `next.config.mjs`
- `tailwind.config.ts`
- `postcss.config.js`
- `app/layout.tsx`
- `app/page.tsx`
- `components/Sidebar.tsx`
- `components/TopNav.tsx`
- `components/StatCard.tsx`
- `components/DataTable.tsx`
- `components/GlassPanel.tsx`
- `hooks/useDashboardData.ts`
- `lib/api.ts`
- `prisma/schema.prisma`

This design spec is ready to guide the dashboard build and the enterprise-grade admin experience.