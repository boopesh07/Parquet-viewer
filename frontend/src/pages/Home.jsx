import { Link } from 'react-router-dom';
import { 
  ArrowPathIcon, 
  BoltIcon, 
  ShieldCheckIcon, 
  CurrencyDollarIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { useEffect } from 'react';
import ReactGA from 'react-ga4';

const features = [
  {
    name: 'Lightning Fast',
    description: 'Stream large files efficiently with optimized conversion algorithms.',
    icon: BoltIcon,
  },
  {
    name: 'Secure & Private',
    description: 'No data stored. All processing happens securely without saving your files.',
    icon: ShieldCheckIcon,
  },
  {
    name: 'Free Forever',
    description: 'No signup required. Convert up to 5 files at once, each up to 500MB.',
    icon: CurrencyDollarIcon,
  },
  {
    name: 'Multiple Formats',
    description: 'Convert between Parquet, CSV, and NDJSON formats seamlessly.',
    icon: ArrowPathIcon,
  },
];

const converters = [
  {
    title: 'Parquet to CSV',
    description: 'Open Parquet files in Excel and Google Sheets',
    path: '/parquet-to-csv',
    fromFormat: 'Parquet',
    toFormat: 'CSV',
  },
  {
    title: 'CSV to Parquet',
    description: 'Convert CSV to columnar Parquet format',
    path: '/csv-to-parquet',
    fromFormat: 'CSV',
    toFormat: 'Parquet',
  },
  {
    title: 'NDJSON to CSV',
    description: 'Transform newline-delimited JSON to CSV',
    path: '/ndjson-to-csv',
    fromFormat: 'NDJSON',
    toFormat: 'CSV',
  },
  {
    title: 'CSV to NDJSON',
    description: 'Convert CSV to newline-delimited JSON',
    path: '/csv-to-ndjson',
    fromFormat: 'CSV',
    toFormat: 'NDJSON',
  },
];

function Home() {
  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: '/' });
  }, []);

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-800 dark:to-gray-900 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6">
              Convert Data Files Instantly
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
              Fast, free, and secure online converter for Parquet, CSV, and NDJSON files.
              No signup required. Process large files up to 500MB with ease.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link to="/parquet-to-csv" className="btn-primary inline-flex items-center justify-center">
                Start Converting
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
              <a href="#converters" className="btn-secondary inline-flex items-center justify-center">
                View All Tools
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose ParquetFormatter?
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              The fastest and most reliable way to convert your data files
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div
                key={feature.name}
                className="card hover:shadow-xl transition-shadow duration-200"
              >
                <feature.icon className="h-12 w-12 text-primary-600 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.name}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Converters Section */}
      <section id="converters" className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Available Converters
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Choose your conversion tool below
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {converters.map((converter) => (
              <Link
                key={converter.path}
                to={converter.path}
                className="card hover:shadow-xl transition-all duration-200 hover:scale-105 group"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {converter.title}
                  </h3>
                  <ArrowRightIcon className="h-6 w-6 text-primary-600 group-hover:translate-x-2 transition-transform" />
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {converter.description}
                </p>
                <div className="flex items-center space-x-3 text-sm">
                  <span className="px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded-full font-medium">
                    {converter.fromFormat}
                  </span>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400" />
                  <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full font-medium">
                    {converter.toFormat}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* SEO Content Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="prose dark:prose-invert max-w-none">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
              About Parquet, CSV, and NDJSON Formats
            </h2>
            
            <div className="space-y-6 text-gray-600 dark:text-gray-400">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  What is Parquet?
                </h3>
                <p>
                  Apache Parquet is a columnar storage format optimized for analytics and big data processing.
                  It's widely used in data engineering pipelines with tools like Apache Spark, AWS Athena, and
                  Google BigQuery. However, traditional spreadsheet tools like Excel and Google Sheets cannot
                  open Parquet files directly, making conversion to CSV essential for data analysis.
                </p>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  What is NDJSON?
                </h3>
                <p>
                  NDJSON (Newline Delimited JSON) is a format where each line is a valid JSON object.
                  It's perfect for streaming data, log files, and machine learning datasets. Converting
                  NDJSON to CSV makes it accessible in spreadsheet applications for easy viewing and analysis.
                </p>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Why Convert Data Files?
                </h3>
                <p>
                  Data teams frequently need to convert between formats: Parquet for storage efficiency,
                  CSV for universal compatibility, and NDJSON for streaming workflows. Our converter handles
                  these transformations instantly, supporting files up to 500MB with no signup required.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;