import { useEffect } from 'react';
import FileConverter from '../components/FileConverter';
import { trackPageview } from '../lib/analytics';
import { usePageMeta } from '../hooks/usePageMeta';

function NdjsonToCsv() {
  usePageMeta({
    title: 'NDJSON to CSV Converter & Viewer | ParquetFormatter',
    description: 'Transform NDJSON or JSONL files and URLs into flattened CSV exports ready for Excel or Sheets.',
    keywords: ['ndjson viewer', 'ndjson to csv', 'jsonl viewer', 'ndjson converter'],
  });

  useEffect(() => {
    trackPageview('/ndjson-to-csv');
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
