# TikTok Auto Poster - Frontend

A modern Next.js 15 dashboard for managing TikTok automated posting campaigns.

## Features

- Dashboard with real-time statistics
- Account management with import functionality
- Proxy management with health checks
- Campaign creation and scheduling
- Job queue monitoring
- Settings configuration
- Dark theme with purple/blue accents
- Fully responsive design

## Tech Stack

- **Next.js 15** - React framework with App Router
- **React 19** - Latest React version
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **React Dropzone** - File upload
- **Lucide React** - Icons
- **date-fns** - Date formatting

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running (default: http://localhost:8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Update the API URL in `.env.local` if needed:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:
```bash
npm run build
```

Start production server:
```bash
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── accounts/          # Account management
│   │   ├── campaigns/         # Campaign management
│   │   │   └── new/          # New campaign form
│   │   ├── jobs/             # Jobs queue
│   │   ├── proxies/          # Proxy management
│   │   ├── settings/         # Settings
│   │   ├── layout.tsx        # Root layout with sidebar
│   │   ├── page.tsx          # Dashboard
│   │   └── globals.css       # Global styles
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Badge.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Table.tsx
│   │   │   └── Tabs.tsx
│   │   └── Sidebar.tsx       # Navigation sidebar
│   └── lib/
│       ├── api.ts            # API client and endpoints
│       └── utils.ts          # Utility functions
├── tailwind.config.ts        # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies
```

## Pages

### Dashboard (/)
- Overview statistics for accounts, proxies, campaigns
- Job statistics (pending, running, completed, failed)
- Recent activity feed

### Accounts (/accounts)
- List all TikTok accounts
- Import accounts from CSV
- Filter by status
- View account details and stats

### Proxies (/proxies)
- List all proxies
- Import proxies from TXT file
- Health check functionality
- View latency and status

### Campaigns (/campaigns)
- List all campaigns
- Create new campaigns with:
  - Multiple video uploads
  - Caption templates
  - Account selection (all/random/specific)
  - Schedule configuration
  - Delay settings
- Start/pause/delete campaigns
- View campaign progress

### Jobs (/jobs)
- Monitor all posting jobs
- Filter by status
- Retry failed jobs
- Cancel pending/running jobs
- View job details and errors

### Settings (/settings)
- General settings
- Upload configuration
- Notification preferences

## API Integration

The frontend connects to the backend API via Axios. API endpoints are defined in `src/lib/api.ts`.

Default API URL: `http://localhost:8000/api`

### API Endpoints

- `GET /accounts` - List accounts
- `POST /accounts/import` - Import accounts
- `GET /proxies` - List proxies
- `POST /proxies/import` - Import proxies
- `POST /proxies/:id/health-check` - Check proxy health
- `GET /campaigns` - List campaigns
- `POST /campaigns` - Create campaign
- `POST /campaigns/:id/start` - Start campaign
- `POST /campaigns/:id/pause` - Pause campaign
- `GET /jobs` - List jobs
- `POST /jobs/:id/retry` - Retry job
- `POST /jobs/:id/cancel` - Cancel job
- `GET /stats/dashboard` - Dashboard statistics

## Styling

The app uses a custom dark theme with purple and blue accents:

- Background: `#0a0a0f`
- Surface: `#131318`
- Border: `#2a2a35`
- Primary: Purple scale (`#8b5cf6` - `#4c1d95`)
- Accent: Blue scale (`#3b82f6` - `#1e3a8a`)

## Components

All UI components are built with accessibility in mind and support:
- Keyboard navigation
- Focus states
- ARIA attributes
- Responsive design

## License

MIT
