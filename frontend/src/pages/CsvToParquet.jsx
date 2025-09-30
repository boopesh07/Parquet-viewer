import { useEffect } from 'react';
import ReactGA from 'react-ga4';
import FileConverter from '../components/FileConverter';

function CsvToParquet() {
  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: '/csv-to-parquet' });
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