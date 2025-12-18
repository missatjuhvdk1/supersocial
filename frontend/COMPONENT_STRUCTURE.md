# Component Structure & Design Documentation

## UI Component Hierarchy

### Core Layout Components

```
RootLayout
├── Providers (React Query)
├── Sidebar
│   ├── Logo
│   ├── Navigation Links
│   │   ├── Dashboard
│   │   ├── Accounts
│   │   ├── Proxies
│   │   ├── Campaigns
│   │   ├── Jobs
│   │   └── Settings
│   └── User Profile
└── Main Content Area
    └── [Page Components]
```

---

## Page Components

### 1. Dashboard Page (`/`)

**Component Structure:**
```
DashboardPage
├── Stats Cards Grid
│   ├── AccountsCard (total, active, inactive)
│   ├── ProxiesCard (total, working, failed)
│   └── CampaignsCard (total, active, completed)
├── Job Statistics Card
│   ├── Pending Count
│   ├── Running Count
│   ├── Completed Count
│   └── Failed Count
└── Recent Activity Card
    └── Activity List Items
```

**Props Interface:**
```typescript
interface DashboardStats {
  accounts: { total: number; active: number; inactive: number };
  proxies: { total: number; working: number; failed: number };
  campaigns: { total: number; active: number; completed: number };
  jobs: { pending: number; running: number; completed: number; failed: number };
}
```

**Accessibility:**
- ARIA labels for stat cards
- Keyboard navigation for activity items
- Screen reader announcements for real-time updates

**Responsive Breakpoints:**
- Mobile (< 768px): Single column
- Tablet (768px - 1024px): 2 columns
- Desktop (> 1024px): 3 columns

---

### 2. Accounts Page (`/accounts`)

**Component Structure:**
```
AccountsPage
├── Header (title + Import button)
├── AccountsCard
│   ├── CardHeader (title + status filter)
│   └── Table
│       ├── TableHeader (columns)
│       └── TableBody
│           └── AccountRow[]
│               ├── Email
│               ├── Username
│               ├── Status Badge
│               ├── Proxy
│               ├── Post Count
│               ├── Last Used
│               └── Actions (refresh, delete)
└── ImportModal
    ├── File Upload Zone
    └── Footer (cancel, import buttons)
```

**Props Interface:**
```typescript
interface Account {
  id: string;
  email: string;
  username: string;
  status: 'active' | 'inactive' | 'banned' | 'pending';
  proxy: string | null;
  lastUsed: string | null;
  postsCount: number;
}
```

**Accessibility:**
- Table with proper headers
- Row selection with keyboard
- Modal trap focus
- File input with label association

**Responsive:**
- Mobile: Horizontal scroll table
- Tablet+: Full width table

---

### 3. Proxies Page (`/proxies`)

**Component Structure:**
```
ProxiesPage
├── Header (title + Check All + Import buttons)
├── ProxiesCard
│   └── Table
│       └── ProxyRow[]
│           ├── Host:Port
│           ├── Type Badge
│           ├── Username
│           ├── Status Badge
│           ├── Latency Badge
│           ├── Last Checked
│           └── Actions (health check, delete)
└── ImportModal
```

**Props Interface:**
```typescript
interface Proxy {
  id: string;
  host: string;
  port: number;
  type: 'http' | 'https' | 'socks5';
  username: string | null;
  status: 'working' | 'failed' | 'checking';
  latency: number | null;
  lastChecked: string;
}
```

**Accessibility:**
- Status indicators with text labels
- Loading states for health checks
- Clear error messages

**Responsive:**
- Mobile: Scroll table or card view
- Desktop: Full table view

---

### 4. Campaigns Page (`/campaigns`)

**Component Structure:**
```
CampaignsPage
├── Header (title + New Campaign button)
└── CampaignsCard
    └── Table
        └── CampaignRow[]
            ├── Name
            ├── Status Badge
            ├── Video Count
            ├── Account Count
            ├── Progress Bar
            ├── Schedule
            ├── Created Date
            └── Actions (play/pause, delete)
```

**Props Interface:**
```typescript
interface Campaign {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed';
  videosCount: number;
  accountsCount: number;
  completedJobs: number;
  totalJobs: number;
  schedule: string;
  createdAt: string;
}
```

---

### 5. New Campaign Page (`/campaigns/new`)

**Component Structure:**
```
NewCampaignPage
└── Form
    ├── BasicInfoCard
    │   ├── Name Input
    │   └── Caption Textarea
    ├── VideosCard
    │   ├── Dropzone
    │   └── Video List
    │       └── VideoItem[]
    │           ├── Video Icon
    │           ├── Name & Size
    │           └── Remove Button
    ├── AccountSelectionCard
    │   ├── Selection Mode Select
    │   ├── Random Count Input (conditional)
    │   └── Account Checkboxes (conditional)
    ├── ScheduleCard
    │   ├── Time Range (start/end)
    │   └── Delay Range (min/max)
    └── Footer (cancel, create buttons)
```

**Form State:**
```typescript
interface CampaignForm {
  name: string;
  caption: string;
  accountSelection: 'all' | 'random' | 'specific';
  randomCount?: number;
  selectedAccounts?: string[];
  scheduleStart: string;
  scheduleEnd: string;
  delayMin: number;
  delayMax: number;
  videos: File[];
}
```

**Accessibility:**
- Form validation with error messages
- Drag-and-drop with keyboard alternative
- Clear focus indicators
- Progress indication during upload

**Responsive:**
- Mobile: Full width cards, stacked inputs
- Tablet+: Side-by-side inputs where appropriate

---

### 6. Jobs Page (`/jobs`)

**Component Structure:**
```
JobsPage
├── Header
└── JobsCard
    ├── CardHeader (title + status filter)
    └── Table
        └── JobRow[]
            ├── Campaign Name
            ├── Account Email
            ├── Video Name
            ├── Status Badge + Error
            ├── Progress Bar
            ├── Scheduled For
            ├── Started At
            └── Actions (view, retry, cancel)
```

**Props Interface:**
```typescript
interface Job {
  id: string;
  campaignName: string;
  accountEmail: string;
  videoName: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  scheduledFor: string;
  startedAt: string | null;
  completedAt: string | null;
  error: string | null;
}
```

---

### 7. Settings Page (`/settings`)

**Component Structure:**
```
SettingsPage
├── Header
└── Tabs
    ├── GeneralTab
    │   ├── API URL Input
    │   ├── Concurrent Jobs Input
    │   ├── Timeout Input
    │   ├── Retry Attempts Input
    │   └── Save Button
    ├── UploadTab
    │   ├── Upload Timeout Input
    │   ├── Max Size Input
    │   ├── Allowed Formats Input
    │   ├── Auto Thumbnail Toggle
    │   └── Save Button
    └── NotificationsTab
        ├── Email Toggle
        ├── Email Address Input (conditional)
        ├── Success Notifications Checkbox
        ├── Failure Notifications Checkbox
        └── Save Button
```

---

## Reusable UI Components

### Button Component

**Props:**
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  children: ReactNode;
}
```

**Variants:**
- Primary: Purple background (main actions)
- Secondary: Outlined (cancel, secondary actions)
- Danger: Red background (delete, destructive)
- Ghost: Transparent (icon buttons)

**States:**
- Default, Hover, Focus, Active, Disabled, Loading

---

### Card Component

**Props:**
```typescript
interface CardProps {
  children: ReactNode;
  className?: string;
}

interface CardHeaderProps {
  children: ReactNode;
}

interface CardTitleProps {
  children: ReactNode;
}

interface CardContentProps {
  children: ReactNode;
}
```

**Usage:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

---

### Badge Component

**Props:**
```typescript
interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default';
  children: ReactNode;
}
```

**Color Mapping:**
- Success: Green (active, completed, working)
- Warning: Yellow (paused, pending)
- Error: Red (failed, banned, error)
- Info: Blue (running, checking)
- Default: Gray (neutral states)

---

### Modal Component

**Props:**
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  footer?: ReactNode;
}
```

**Features:**
- Focus trap
- Escape key to close
- Backdrop click to close
- Scroll lock on body
- Keyboard navigation

**Accessibility:**
- role="dialog"
- aria-modal="true"
- aria-labelledby for title
- Focus management

---

### Table Component

**Props:**
```typescript
interface TableProps {
  children: ReactNode;
}
// Similar for TableHeader, TableBody, TableRow, TableHead, TableCell
```

**Features:**
- Responsive horizontal scroll
- Hover states on rows
- Semantic HTML (thead, tbody, tr, th, td)
- Proper column headers

---

### Input Component

**Props:**
```typescript
interface InputProps {
  label?: string;
  error?: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
}
```

**Features:**
- Label association
- Error state styling
- Error message display
- Focus states
- Placeholder support

---

### Select Component

**Props:**
```typescript
interface SelectProps {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
}
```

---

### Tabs Component

**Props:**
```typescript
interface TabsProps {
  defaultValue: string;
  children: ReactNode;
}

interface TabsTriggerProps {
  value: string;
  children: ReactNode;
}

interface TabsContentProps {
  value: string;
  children: ReactNode;
}
```

**Usage:**
```tsx
<Tabs defaultValue="general">
  <TabsList>
    <TabsTrigger value="general">General</TabsTrigger>
    <TabsTrigger value="upload">Upload</TabsTrigger>
  </TabsList>
  <TabsContent value="general">Content</TabsContent>
  <TabsContent value="upload">Content</TabsContent>
</Tabs>
```

---

## Animation & Transitions

### Loading States
- Spinner animation on buttons
- Skeleton loaders for table rows
- Progress bars for file uploads

### Transitions
- 150ms ease-in-out for hover states
- 200ms for modal open/close
- 300ms for sidebar toggle (if implemented)

### Animations
- Fade in for modals
- Slide up for toasts/notifications
- Pulse for loading indicators

---

## Responsive Breakpoint Strategy

```css
/* Mobile First Approach */
sm: 640px   /* Small devices */
md: 768px   /* Tablets */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large screens */
```

### Layout Strategy
- Mobile (< 768px): Sidebar collapsed to hamburger, single column
- Tablet (768px - 1024px): Full sidebar, 2 columns
- Desktop (> 1024px): Full sidebar, 3 columns, expanded tables

---

## WCAG Accessibility Compliance

### Level AA Requirements Met

1. **Keyboard Navigation**
   - All interactive elements accessible via Tab
   - Modal focus trap
   - Skip to main content (can be added)

2. **Focus Indicators**
   - 2px outline with primary-500 color
   - Visible on all interactive elements

3. **Color Contrast**
   - Text: 7:1 ratio (white on dark background)
   - Interactive elements: 4.5:1 minimum

4. **ARIA Attributes**
   - role="dialog" on modals
   - aria-label on icon buttons
   - aria-describedby for form errors
   - aria-live for dynamic content

5. **Semantic HTML**
   - Proper heading hierarchy (h1 → h2 → h3)
   - Table headers with scope
   - Form labels associated with inputs

6. **Form Validation**
   - Clear error messages
   - Error state styling
   - Required field indicators

---

## Form Validation & Error Handling UX

### Input Validation
```typescript
// Real-time validation on blur
// Show errors immediately
// Clear errors on correct input
```

### Error Display
- Inline errors below inputs
- Red border on invalid fields
- Clear error messages (not just "Invalid")

### Success Feedback
- Toast notifications (can be added)
- Success badges
- Redirect on success

---

## Loading States & Skeletons

### Button Loading
- Spinner icon
- Disabled state
- "Loading..." text (optional)

### Page Loading
- Skeleton cards for dashboard
- Skeleton rows for tables
- Shimmer effect

### Progress Indication
- Progress bars for uploads
- Percentage display
- Time remaining (for long operations)

---

## Component API Summary

| Component | Required Props | Optional Props | Events |
|-----------|---------------|----------------|---------|
| Button | children | variant, size, isLoading, disabled | onClick |
| Card | children | className | - |
| Badge | children | variant | - |
| Modal | isOpen, onClose, title, children | size, footer | - |
| Input | value, onChange | label, error, type, placeholder | onChange, onBlur |
| Select | options, value, onChange | label, error | onChange |
| Table | children | - | - |
| Tabs | defaultValue, children | - | - |

---

## Theme Customization

### Color System
```typescript
colors: {
  background: '#0a0a0f',
  surface: '#131318',
  'surface-hover': '#1a1a22',
  border: '#2a2a35',
  primary: { 50: '#f5f3ff', ..., 900: '#4c1d95' },
  accent: { 50: '#eff6ff', ..., 900: '#1e3a8a' },
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  muted: '#6b7280',
}
```

### Typography
- Font: Inter (sans-serif)
- Sizes: 12px, 14px, 16px, 18px, 24px, 30px

### Spacing
- Consistent 8px grid system
- Padding: p-2 (8px), p-4 (16px), p-6 (24px), p-8 (32px)
- Gap: gap-2, gap-3, gap-4, gap-6

---

## Future Enhancement Recommendations

1. **Add Toast/Notification System**
   - Success/error notifications
   - Auto-dismiss
   - Stack multiple notifications

2. **Add Confirmation Dialogs**
   - Before delete actions
   - Before cancel operations
   - Custom confirmation messages

3. **Add Tooltip Component**
   - Icon explanations
   - Disabled button reasons
   - Additional context

4. **Add Date Picker**
   - Campaign scheduling
   - Date range filters

5. **Add Multi-Select Component**
   - Account selection
   - Bulk operations

6. **Add Search/Filter**
   - Search accounts by email
   - Filter campaigns by date
   - Global search

7. **Add Pagination**
   - Table pagination
   - Load more button
   - Infinite scroll

8. **Add Export Functionality**
   - Export tables to CSV
   - Export reports
   - Download logs

---

## Testing Recommendations

### Component Testing
- Unit tests for UI components
- Prop validation
- Event handler testing

### Integration Testing
- Form submission flows
- API integration
- Navigation

### Accessibility Testing
- Screen reader compatibility
- Keyboard navigation
- Color contrast

### Responsive Testing
- Mobile devices (320px - 768px)
- Tablets (768px - 1024px)
- Desktops (1024px+)
