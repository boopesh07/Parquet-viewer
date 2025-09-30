import { useEffect } from 'react';
import FileConverter from '../components/FileConverter';
import { trackPageview } from '../lib/analytics';
import { usePageMeta } from '../hooks/usePageMeta';

function CsvToNdjson() {
  usePageMeta({
    title: 'CSV to NDJSON Converter | ParquetFormatter',
    description: 'Quickly convert CSV files or URLs into streaming-friendly NDJSON output.',
    keywords: ['csv to ndjson', 'ndjson converter', 'csv converter', 'jsonl converter'],
  });

  useEffect(() => {
    trackPageview('/csv-to-ndjson');
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
