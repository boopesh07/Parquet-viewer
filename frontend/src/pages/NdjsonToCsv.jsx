import { useEffect } from 'react';
import ReactGA from 'react-ga4';
import FileConverter from '../components/FileConverter';

function NdjsonToCsv() {
  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: '/ndjson-to-csv' });
  }, []);

  return (
    <FileConverter
      title="NDJSON to CSV Converter"
      description="Convert NDJSON (Newline Delimited JSON) or JSONL files to CSV format. Ideal for log files, streaming data, and machine learning datasets."
      acceptedFormats={['.ndjson', '.jsonl']}
      endpoint="/v1/convert/ndjson-to-csv"
      outputFormat=".csv"
      maxFiles={5}
    />
  );
}

export default NdjsonToCsv;