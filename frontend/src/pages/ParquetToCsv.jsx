import { useEffect } from 'react';
import FileConverter from '../components/FileConverter';
import { trackPageview } from '../lib/analytics';
import { usePageMeta } from '../hooks/usePageMeta';

function ParquetToCsv() {
  usePageMeta({
    title: 'Parquet to CSV Converter & Viewer | ParquetFormatter',
    description: 'Upload files or URLs to convert Parquet files to CSV or preview them instantly in your browser.',
    keywords: ['parquet viewer', 'parquet to csv', 'parquet converter', 'online parquet viewer'],
  });

  useEffect(() => {
    trackPageview('/parquet-to-csv');
  }, []);

  return (
    <FileConverter
      title="Parquet to CSV Converter"
      description="Convert Parquet files to CSV format for easy viewing in Excel, Google Sheets, or any spreadsheet application. Upload up to 5 files at once."
      acceptedFormats={['.parquet']}
      endpoint="/v1/convert/parquet-to-csv"
      outputFormat=".csv"
      maxFiles={5}
    />
  );
}

export default ParquetToCsv;
