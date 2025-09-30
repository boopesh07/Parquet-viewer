import { useEffect } from 'react';
import FileConverter from '../components/FileConverter';
import { trackPageview } from '../lib/analytics';
import { usePageMeta } from '../hooks/usePageMeta';

function CsvToParquet() {
  usePageMeta({
    title: 'CSV to Parquet Converter | ParquetFormatter',
    description: 'Convert CSV files or URLs into high-performance Parquet format for analytics workflows.',
    keywords: ['csv to parquet', 'parquet converter', 'csv converter', 'csv parquet viewer'],
  });

  useEffect(() => {
    trackPageview('/csv-to-parquet');
  }, []);

  return (
    <FileConverter
      title="CSV to Parquet Converter"
      description="Convert CSV files to Apache Parquet format for efficient columnar storage and analytics. Perfect for big data workflows with Spark, Athena, and BigQuery."
      acceptedFormats={['.csv']}
      endpoint="/v1/convert/csv-to-parquet"
      outputFormat=".parquet"
      maxFiles={5}
    />
  );
}

export default CsvToParquet;
