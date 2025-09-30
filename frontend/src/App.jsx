import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import ParquetToCsv from './pages/ParquetToCsv';
import CsvToParquet from './pages/CsvToParquet';
import NdjsonToCsv from './pages/NdjsonToCsv';
import CsvToNdjson from './pages/CsvToNdjson';
import { initAnalytics } from './lib/analytics';

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;
initAnalytics(GA_MEASUREMENT_ID);

function App() {
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
