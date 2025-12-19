# TikTok Auto Poster Frontend - Quick Start Guide

## Installation & Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- React Query
- Axios
- React Dropzone
- Lucide React icons
- date-fns

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Project Overview

### Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard with statistics and recent activity |
| `/accounts` | TikTok account management |
| `/proxies` | Proxy pool management |
| `/campaigns` | Campaign list and management |
| `/campaigns/new` | Create new posting campaign |
| `/jobs` | Job queue monitoring |
| `/settings` | Application settings |

### Key Features

**Dashboard**
- Real-time statistics for accounts, proxies, campaigns
- Job status overview
- Recent activity feed

**Accounts Page**
- Import accounts from CSV file
- View account status and last usage
- Filter by status (active/inactive/banned)
- Delete accounts

**Proxies Page**
- Import proxies from TXT file
- Health check functionality
- View latency and status
- Delete proxies

**Campaigns Page**
- Create campaigns with multiple videos
- Configure posting schedule
- Select accounts (all/random/specific)
- Set delay between posts
- Start/pause/delete campaigns
- View progress

**Jobs Page**
- Monitor all posting jobs
- Filter by status
- Retry failed jobs
- Cancel pending/running jobs

**Settings Page**
- Configure API settings
- Upload preferences
- Notification settings

---

## File Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── accounts/          # Account management page
│   │   ├── campaigns/         # Campaign pages
│   │   │   ├── page.tsx      # List campaigns
│   │   │   └── new/          # New campaign form
│   │   ├── jobs/             # Jobs queue page
│   │   ├── proxies/          # Proxy management page
│   │   ├── settings/         # Settings page
│   │   ├── layout.tsx        # Root layout with sidebar
│   │   ├── page.tsx          # Dashboard
│   │   ├── providers.tsx     # React Query provider
│   │   └── globals.css       # Global styles
│   │
│   ├── components/
│   │   ├── Sidebar.tsx       # Main navigation
│   │   └── ui/               # Reusable components
│   │       ├── Badge.tsx
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       ├── Select.tsx
│   │       ├── Table.tsx
│   │       └── Tabs.tsx
│   │
│   └── lib/
│       ├── api.ts            # API client & endpoints
│       └── utils.ts          # Utility functions
│
├── tailwind.config.ts        # Tailwind theme config
├── tsconfig.json            # TypeScript config
└── package.json             # Dependencies
```

---

## Component Usage Examples

### Button

```tsx
import Button from '@/components/ui/Button';

// Primary button
<Button variant="primary" onClick={handleClick}>
  Click Me
</Button>

// Loading state
<Button isLoading={isSubmitting}>
  Submit
</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
```

### Card

```tsx
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content goes here
  </CardContent>
</Card>
```

### Modal

```tsx
import Modal from '@/components/ui/Modal';

const [isOpen, setIsOpen] = useState(false);

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
  footer={
    <>
      <Button variant="secondary" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button onClick={handleSubmit}>
        Confirm
      </Button>
    </>
  }
>
  Modal content
</Modal>
```

### Table

```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Item 1</TableCell>
      <TableCell>Active</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### Input

```tsx
import Input from '@/components/ui/Input';

<Input
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  error={errors.email}
  placeholder="Enter email"
/>
```

---

## API Integration

The frontend uses Axios with React Query for data fetching.

### API Client Setup

Located in `src/lib/api.ts`:

```typescript
import api, { accountsAPI, proxiesAPI, campaignsAPI } from '@/lib/api';

// List accounts
const accounts = await accountsAPI.getAll();

// Import accounts
await accountsAPI.import(file);

// Create campaign
await campaignsAPI.create(data);
```

### Using React Query

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsAPI } from '@/lib/api';

// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['accounts'],
  queryFn: accountsAPI.getAll,
});

// Mutations
const queryClient = useQueryClient();
const mutation = useMutation({
  mutationFn: accountsAPI.delete,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['accounts'] });
  },
});
```

---

## Styling Guide

### Dark Theme Colors

```css
Background: #0a0a0f
Surface: #131318
Border: #2a2a35
Primary: #8b5cf6 (purple)
Accent: #3b82f6 (blue)
Success: #10b981 (green)
Warning: #f59e0b (yellow)
Error: #ef4444 (red)
```

### Tailwind Utilities

```tsx
// Card style
className="bg-surface border border-border rounded-lg"

// Hover state
className="hover:bg-surface-hover transition-colors"

// Text colors
className="text-white"      // Primary text
className="text-muted"      // Secondary text

// Spacing
className="p-6"             // Padding
className="gap-4"           // Gap between flex/grid items
```

---

## Common Tasks

### Add a New Page

1. Create file: `src/app/my-page/page.tsx`
2. Add route to sidebar: `src/components/Sidebar.tsx`
3. Create API endpoints: `src/lib/api.ts`

### Add a New Component

1. Create file: `src/components/ui/MyComponent.tsx`
2. Export component with props interface
3. Use Tailwind for styling
4. Follow accessibility guidelines

### Modify the Theme

Edit `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      // Add your colors
    }
  }
}
```

---

## Development Tips

### Hot Reload
- Changes auto-reload in development
- Fast Refresh preserves component state

### Type Safety
- Use TypeScript interfaces for all data
- Enable strict mode in tsconfig.json
- Leverage IDE autocomplete

### Code Organization
- Keep components small and focused
- Extract reusable logic to custom hooks
- Use React Query for server state
- Use useState for UI state

### Performance
- Use React.memo for expensive renders
- Lazy load images and videos
- Debounce search inputs
- Paginate large lists

---

## Build & Deploy

### Development Build
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Static Export (if needed)
Add to `next.config.js`:
```javascript
module.exports = {
  output: 'export',
}
```

---

## Troubleshooting

### Port Already in Use
```bash
# Use different port
PORT=3001 npm run dev
```

### API Connection Issues
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify backend is running
- Check CORS settings on backend

### Styling Issues
- Clear .next folder: `rm -rf .next`
- Rebuild: `npm run build`
- Check Tailwind config

### Type Errors
- Run type check: `npx tsc --noEmit`
- Update TypeScript: `npm update typescript`

---

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev/)

---

## Support

For issues or questions:
1. Check COMPONENT_STRUCTURE.md for detailed component docs
2. Review README.md for full documentation
3. Check console for error messages
4. Verify API is responding correctly
