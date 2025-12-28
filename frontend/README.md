# RMI Audit Toolkit - Frontend

Modern React frontend for the RMI Audit Toolkit, built with NextBelt's industrial design system.

## Design System

Matches the NextBelt website aesthetic:
- **Colors**: Deep teal primary (#0D4F4F), warm copper accent (#C65D3B)
- **Typography**: Space Grotesk (headings/body) + IBM Plex Mono (technical)
- **Style**: Clean, editorial layouts with industrial feel

## Features

- **Dashboard**: Assessment overview and management
- **Interview Interface**: Structured questionnaire with scoring
- **Observation Checklist**: Real-time field compliance tracking
- **Assessment Detail**: Comprehensive RMI scoring and reporting
- **CMMS Upload**: Automated data analysis integration

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- React Router (routing)
- Zustand (state management)
- Axios (API client)
- Recharts (data visualization)

## Getting Started

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and state management
│   ├── components/    # Reusable UI components
│   ├── views/         # Page components
│   ├── styles/        # Theme and global styles
│   ├── App.tsx        # Main app with routing
│   └── main.tsx       # Entry point
├── package.json
└── vite.config.ts
```

## API Integration

The frontend connects to the FastAPI backend running on `http://localhost:8000`. Configure the API URL in `.env`:

```
VITE_API_URL=http://localhost:8000
```

## Authentication

Uses JWT tokens stored in localStorage. Protected routes automatically redirect to login if unauthenticated.

**Demo Credentials:**
- Email: admin@nextbelt.com
- Password: admin123

## Components

### Core Components
- **Button**: Primary, secondary, outline, text variants
- **Card**: Hoverable content containers
- **Input/TextArea**: Form inputs with validation
- **Modal**: Overlay dialogs

### Views
- **Login**: Authentication page
- **Dashboard**: Assessment list and creation
- **AssessmentDetail**: RMI scoring and radar chart
- **InterviewInterface**: Question-by-question wizard
- **ObservationChecklist**: Tablet-friendly field checklists

## License

© 2024 NextBelt LLC
