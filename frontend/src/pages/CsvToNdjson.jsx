import { useEffect } from 'react';
import ReactGA from 'react-ga4';
import FileConverter from '../components/FileConverter';

function CsvToNdjson() {
  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: '/csv-to-ndjson' });
  }, []);

  return (
    <FileConverter
      title="CSV to NDJSON Converter"
      description="Convert CSV files to NDJSON (Newline Delimited JSON) format for streaming data pipelines and log processing systems."
      acceptedFormats={['.csv']}
      endpoint="/v1/convert/csv-to-ndjson"
      outputFormat=".ndjson"
      maxFiles={5}
    />
  );
}

export default CsvToNdjson;