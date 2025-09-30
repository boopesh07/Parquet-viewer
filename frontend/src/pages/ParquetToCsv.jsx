import { useEffect } from 'react';
import ReactGA from 'react-ga4';
import FileConverter from '../components/FileConverter';

function ParquetToCsv() {
  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: '/parquet-to-csv' });
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