# ParquetFormatter.com

Fast, free, and secure online converter for Parquet, CSV, and NDJSON files.

## 🚀 Features

### Core Functionality
- **Parquet ↔ CSV Conversion**: Convert between Parquet and CSV formats seamlessly
- **NDJSON ↔ CSV Conversion**: Transform newline-delimited JSON to/from CSV
- **Batch Processing**: Upload and convert up to 5 files at once
- **Large File Support**: Handle files up to 500MB each
- **Data Preview**: View schema and first 50 rows before conversion
- **No Signup Required**: Start converting immediately

### UI/UX Features
- **Modern, Elegant Design**: Built with Tailwind CSS and Headless UI
- **Dark Mode**: System-based detection + manual toggle with localStorage persistence
- **Responsive**: Works perfectly on desktop, tablet, and mobile
- **Drag & Drop**: Intuitive file upload experience
- **Progress Indicators**: Clear feedback during conversion
- **Feedback Widget**: Floating feedback button for user input

### Analytics & Tracking
- **Vercel Web Analytics**: Privacy-friendly visitor and conversion tracking
- **Custom Events**: Track file uploads, conversions, downloads, and feedback
- **Session Tracking**: Monitor user behavior and engagement
- **Page-specific Analytics**: Detailed insights per converter page

### Technical Features
- **Streaming Processing**: Efficient handling of large files
- **Private & Secure**: No data stored on servers
- **SEO Optimized**: Comprehensive meta tags and structured data
- **Fast Performance**: Optimized build with Vite and React

## 📁 Project Structure

```
/app/
├── backend/                    # FastAPI Backend
│   ├── server.py              # Server entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Backend environment variables
│   └── parquetformatter_api/  # Main API application
│       ├── app/
│       │   ├── main.py        # FastAPI app setup
│       │   ├── config.py      # Configuration settings
│       │   ├── routes/        # API endpoints
│       │   │   ├── convert.py # Conversion endpoints
│       │   │   ├── preview.py # Preview endpoint
│       │   │   └── feedback.py# Feedback endpoint
│       │   ├── converters/    # Conversion logic
│       │   │   ├── duck.py    # DuckDB-powered Parquet/CSV
│       │   │   └── polars_ndjson.py # Polars-powered NDJSON
│       │   └── utils/         # Utility functions
│       └── tests/             # Backend tests
│
└── frontend/                  # React Frontend
    ├── src/
    │   ├── App.jsx           # Main app component
    │   ├── main.jsx          # Entry point
    │   ├── index.css         # Global styles
    │   ├── contexts/
    │   │   └── ThemeContext.jsx  # Dark/Light mode
    │   ├── components/
    │   │   ├── Layout.jsx        # App layout with nav
    │   │   ├── FileConverter.jsx # Reusable converter
    │   │   ├── PreviewModal.jsx  # Data preview modal
    │   │   └── FeedbackWidget.jsx# Feedback component
    │   └── pages/
    │       ├── Home.jsx          # Landing page
    │       ├── ParquetToCsv.jsx  # Parquet → CSV
    │       ├── CsvToParquet.jsx  # CSV → Parquet
    │       ├── NdjsonToCsv.jsx   # NDJSON → CSV
    │       └── CsvToNdjson.jsx   # CSV → NDJSON
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.cjs
    ├── postcss.config.cjs
    └── .env                   # Frontend environment variables
```

## 🛠️ Setup & Installation

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
python3 -m venv .venv  # create once
source .venv/bin/activate
pip install -r parquetformatter_api/requirements.txt
```

> If you already have a `.venv`, just activate it before installing.

2. **Start the backend server (local development):**
```bash
cd backend
source .venv/bin/activate
python server.py
```

The backend will run on `http://localhost:8001`

### Frontend Setup

1. **Install Node.js dependencies:**
```bash
cd frontend
yarn install
```

2. **Configure environment variables:**
Edit `frontend/.env`:
```env
VITE_BACKEND_URL=http://localhost:8001
```

3. **Start the frontend server (local development):**
```bash
cd frontend
yarn dev
```

The frontend will run on `http://localhost:3000`

## 📊 Vercel Web Analytics Setup

1. Enable Web Analytics for the project at https://vercel.com
2. Install the analytics package: `yarn add @vercel/analytics`
3. Redeploy the frontend so the `<Analytics />` component is available client-side

### Tracked Events

- **Page Views**: All page navigation
- **File Uploaded**: When users select files
- **File Converted**: Successful conversions
- **File Downloaded**: When converted files are downloaded
- **File Previewed**: When users preview data
- **Submitted Feedback**: When feedback is submitted
- **Conversion Failed**: Failed conversion attempts

## 🎨 Theme System

The app supports both light and dark modes:

- **System Detection**: Automatically detects user's OS preference
- **Manual Toggle**: Theme toggle button in the header
- **Persistence**: Choice saved to localStorage
- **Smooth Transitions**: Animated theme switching

## 🔌 API Endpoints

### Conversion Endpoints
- `POST /v1/convert/parquet-to-csv` - Convert Parquet to CSV
- `POST /v1/convert/csv-to-parquet` - Convert CSV to Parquet
- `POST /v1/convert/ndjson-to-csv` - Convert NDJSON to CSV
- `POST /v1/convert/csv-to-ndjson` - Convert CSV to NDJSON

### Preview Endpoint
- `POST /v1/preview` - Get schema and first 50 rows

### Feedback Endpoint
- `POST /v1/feedback` - Submit user feedback

### Health Check
- `GET /healthz` - Service health status

## 🚀 Deployment

Both frontend and backend are managed by supervisor:

```bash
# Check status
sudo supervisorctl status

# Restart all services
sudo supervisorctl restart all

# View logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

## 🎯 SEO Optimization

The app includes:
- Comprehensive meta tags (title, description, keywords)
- Open Graph tags for social sharing
- Twitter Card tags
- JSON-LD structured data
- Semantic HTML structure
- Fast page load times
- Mobile-responsive design

## 🔒 Security & Privacy

- **No Data Storage**: All conversions happen in-memory
- **Secure Processing**: Files are deleted immediately after conversion
- **No Authentication Required**: Zero friction for users
- **CORS Enabled**: Secure cross-origin requests

## 📝 License

Copyright © 2025 ParquetFormatter.com

## 🙋 Support

Use the feedback widget in the app to:
- Report bugs
- Suggest features
- Ask questions
- Share testimonials

---

Built with ❤️ using FastAPI, React, Tailwind CSS, and DuckDB
