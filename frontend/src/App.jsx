import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import ReactGA from 'react-ga4';
import Layout from './components/Layout';
import Home from './pages/Home';
import ParquetToCsv from './pages/ParquetToCsv';
import CsvToParquet from './pages/CsvToParquet';
import NdjsonToCsv from './pages/NdjsonToCsv';
import CsvToNdjson from './pages/CsvToNdjson';

// Initialize Google Analytics
const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;
if (GA_MEASUREMENT_ID) {
  ReactGA.initialize(GA_MEASUREMENT_ID);
}

function App() {
  useEffect(() => {
    // Track initial page view
    if (GA_MEASUREMENT_ID) {
      ReactGA.send({ hitType: 'pageview', page: window.location.pathname });
    }
  }, []);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/parquet-to-csv" element={<ParquetToCsv />} />
          <Route path="/csv-to-parquet" element={<CsvToParquet />} />
          <Route path="/ndjson-to-csv" element={<NdjsonToCsv />} />
          <Route path="/csv-to-ndjson" element={<CsvToNdjson />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;