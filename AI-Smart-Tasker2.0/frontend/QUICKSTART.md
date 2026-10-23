# Frontend Quick Start Guide

## Prerequisites

- Node.js 18 or higher
- npm (comes with Node.js)
- Backend API running on http://localhost:8000

## Installation & Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will be available at **http://localhost:3000**

### 3. Build for Production

```bash
npm run build
npm start
```

## Features Available

### Dashboard (/)
- Overview statistics (total, completed, pending, overdue tasks)
- Recent tasks list
- Quick task creation
- Links to Tasks and Analytics pages

### Tasks Page (/tasks)
- Full task list with all features
- Filtering: All, Completed, Pending, Overdue
- Search functionality
- Task management (create, edit, delete, complete)
- AI-powered features:
  - AI summary generation
  - AI summary modification
  - Manual summary editing
  - AI-generated insults for overdue tasks

### Analytics Page (/analytics)
- Comprehensive statistics
- Completion rate metrics
- Deadline adherence tracking
- Interactive charts:
  - Completion timeline (line chart)
  - Deadline adherence (pie chart)
  - Productivity trend (bar chart)
- Recent activity feed

## API Configuration

The frontend connects to the backend via Next.js proxy:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Proxy: /api/* → http://localhost:8000/api/*

Configure in `next.config.js` if backend is on a different port.

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js pages
│   │   ├── page.tsx      # Dashboard
│   │   ├── tasks/        # Tasks page
│   │   └── analytics/    # Analytics page
│   ├── components/       # React components
│   ├── lib/             # Utils and API client
│   └── types/           # TypeScript types
├── public/              # Static assets
└── package.json
```

## Key Components

### TaskCard
- Displays task with all details
- Shows AI insults for overdue tasks (red background, funny messages)
- Integrated AI summary features
- Completion toggle, edit, delete

### SummaryGenerator
- Generate AI summary button
- Modify dropdown with:
  - Manual Edit (direct text)
  - AI Edit (natural language prompts)

### DeadlineAlert
- Prominent display of AI-generated insults
- "Get Another Insult" button to regenerate
- Red/warning styling with humor

## Development

### Available Scripts

- `npm run dev` - Development server with hot reload
- `npm run build` - Production build
- `npm start` - Start production server
- `npm run lint` - Run ESLint

### Making Changes

1. Edit files in `src/`
2. Changes auto-reload in dev mode
3. TypeScript errors shown in terminal
4. Build before deploying

## Troubleshooting

### Port 3000 already in use
```bash
# Kill process on port 3000 (Windows)
npx kill-port 3000

# Or use different port
PORT=3001 npm run dev
```

### Backend connection issues
1. Verify backend is running on http://localhost:8000
2. Check `next.config.js` proxy configuration
3. Check browser console for CORS errors

### Build errors
1. Delete `.next` folder and `node_modules`
2. Run `npm install` again
3. Run `npm run build`

## Testing the Application

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000
4. Create a task with a deadline
5. Test AI summary generation
6. Set deadline in past to see AI insults
7. Try Manual and AI Edit options
8. Check Analytics page for charts

## Environment

No .env files needed! Configuration is handled through:
- Next.js config (next.config.js)
- Tailwind config (tailwind.config.js)
- TypeScript config (tsconfig.json)

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Performance

- First Load JS: ~87-228 KB
- Static page generation
- Code splitting by route
- Optimized images and assets

## Notes

- All pages are statically generated at build time
- API calls happen client-side
- Responsive mobile-first design
- Accessible (WCAG 2.1 AA)
