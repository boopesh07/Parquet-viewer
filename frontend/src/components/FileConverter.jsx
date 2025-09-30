import { useMemo, useRef, useState } from 'react';
import {
  ArrowUpTrayIcon,
  DocumentArrowDownIcon,
  XMarkIcon,
  EyeIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import axios from 'axios';
import PreviewModal from './PreviewModal';
import { trackEvent } from '../lib/analytics';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

function FileConverter({
  title,
  description,
  acceptedFormats,
  endpoint,
  outputFormat,
  maxFiles = 5,
}) {
  const [files, setFiles] = useState([]);
  const [urls, setUrls] = useState([]);
  const [urlInput, setUrlInput] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState(null);
  const [previewFile, setPreviewFile] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);
  const sessionId = useMemo(() => {
    if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
      return window.crypto.randomUUID();
    }
    return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }, []);

  const totalItems = files.length + urls.length;
  const remainingSlots = Math.max(maxFiles - totalItems, 0);
  const convertLabel = totalItems > 1
    ? `Convert ${totalItems} Items`
    : `Convert to ${outputFormat.replace('.', '').toUpperCase()}`;

  const recordEvent = (action, value) => {
    trackEvent({ category: 'Conversion', action, label: title, value });
  };

  const sendSessionMetric = async (eventName, attributes = {}) => {
    try {
      await axios.post(`${API_BASE_URL}/v1/metrics/session`, {
        session_id: sessionId,
        event_name: eventName,
        page_path: typeof window !== 'undefined' ? window.location.pathname : undefined,
        attributes,
      });
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn('Metric dispatch skipped', error);
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    addFiles(selectedFiles);
  };

  const addFiles = (newFiles) => {
    setError(null);
    if (!newFiles.length) return;

    if (newFiles.length > remainingSlots) {
      setError(`Maximum ${maxFiles} items allowed (files + URLs). Remove one before adding more.`);
      return;
    }

    const validFiles = newFiles.filter((file) => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      return acceptedFormats.includes(ext);
    });

    if (validFiles.length !== newFiles.length) {
      setError(`Only ${acceptedFormats.join(', ')} files are accepted.`);
    }

    if (!validFiles.length) return;

    setFiles((prev) => [...prev, ...validFiles]);
    recordEvent('File Uploaded', validFiles.length);
    sendSessionMetric('file_uploaded', { count: validFiles.length }).catch(() => {});
  };

  const addUrl = () => {
    const trimmed = urlInput.trim();
    if (!trimmed) return;
    setError(null);

    if (!/^https?:\/\//i.test(trimmed)) {
      setError('Only HTTP(s) URLs are supported.');
      return;
    }

    if (urls.includes(trimmed)) {
      setError('This URL has already been added.');
      return;
    }

    if (remainingSlots < 1) {
      setError(`Maximum ${maxFiles} items allowed (files + URLs). Remove one before adding more.`);
      return;
    }

    setUrls((prev) => [...prev, trimmed]);
    setUrlInput('');
    recordEvent('URL Added', 1);
    sendSessionMetric('url_added', { url: trimmed, endpoint }).catch(() => {});
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const removeUrl = (index) => {
    setUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handlePreviewFile = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post(`${API_BASE_URL}/v1/preview`, formData);
      setPreviewFile({ name: file.name, data: response.data });
      setShowPreview(true);
      recordEvent('File Previewed', 1);
      sendSessionMetric('preview_loaded', { source: 'file', name: file.name }).catch(() => {});
    } catch (err) {
      console.error('Preview failed:', err);
      setError('Failed to preview file. Please try again.');
    }
  };

  const handlePreviewUrl = async (url) => {
    try {
      const formData = new FormData();
      formData.append('url', url);
      const response = await axios.post(`${API_BASE_URL}/v1/preview`, formData);
      setPreviewFile({ name: url, data: response.data });
      setShowPreview(true);
      recordEvent('URL Previewed', 1);
      sendSessionMetric('preview_loaded', { source: 'url' }).catch(() => {});
    } catch (err) {
      console.error('Preview failed:', err);
      setError('Failed to preview URL. Please verify the link and try again.');
    }
  };

  const handleConvert = async () => {
    if (totalItems === 0) {
      setError('Please add at least one file or URL to convert.');
      return;
    }

    setIsConverting(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      urls.forEach((url) => formData.append('urls', url));

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const blob = new Blob([response.data]);
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;

      const disposition = response.headers['content-disposition'];
      let filename = 'converted_output';
      if (disposition) {
        const match = disposition.match(/filename="?([^";]+)"?/i);
        if (match && match[1]) {
          filename = match[1];
        }
      } else if (files.length === 1) {
        const originalName = files[0].name.split('.').slice(0, -1).join('.') || 'converted';
        filename = `${originalName}${outputFormat}`;
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(objectUrl);

      recordEvent('Conversion Completed', totalItems);
      recordEvent('File Downloaded', totalItems);
      await sendSessionMetric('conversion_completed', {
        items: totalItems,
        endpoint,
      });

      setFiles([]);
      setUrls([]);
    } catch (err) {
      console.error('Conversion failed:', err);
      setError(err.response?.data?.detail?.message || 'Conversion failed. Please try again.');
      recordEvent('Conversion Failed', totalItems || 1);
      sendSessionMetric('conversion_failed', {
        items: totalItems,
        endpoint,
        error: err.response?.data?.detail?.code || err.message,
      }).catch(() => {});
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">{title}</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">{description}</p>

        {/* Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          <ArrowUpTrayIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Drop files here or click to browse
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Accepted formats: {acceptedFormats.join(', ')} • Max {maxFiles} items (files + URLs) • Up to 500MB each
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={acceptedFormats.join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* URL Input */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Or add a file by URL (HTTP/HTTPS)
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                <LinkIcon className="h-5 w-5" />
              </div>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com/data.parquet"
                className="input-field pl-10"
              />
            </div>
            <button
              type="button"
              onClick={addUrl}
              className="btn-secondary whitespace-nowrap"
            >
              Add URL
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Remaining slots: {remainingSlots} of {maxFiles} items
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-800 dark:text-red-300 rounded-lg">
            {error}
          </div>
        )}

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-2">
            <h3 className="font-medium text-gray-900 dark:text-white mb-3">
              Uploaded Files ({files.length})
            </h3>
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <DocumentArrowDownIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreviewFile(file);
                    }}
                    className="p-2 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded transition-colors"
                    title="Preview file"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                    title="Remove file"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* URL List */}
        {urls.length > 0 && (
          <div className="mt-6 space-y-2">
            <h3 className="font-medium text-gray-900 dark:text-white mb-3">
              Remote URLs ({urls.length})
            </h3>
            {urls.map((url, index) => (
              <div
                key={`${url}-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <LinkIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {url}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreviewUrl(url);
                    }}
                    className="p-2 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded transition-colors"
                    title="Preview URL"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeUrl(index);
                    }}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                    title="Remove URL"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Convert Button */}
        {totalItems > 0 && (
          <button
            onClick={handleConvert}
            disabled={isConverting}
            className="btn-primary w-full mt-6"
          >
            {isConverting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Converting...
              </span>
            ) : (
              convertLabel
            )}
          </button>
        )}

        {/* Features List */}
        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Features</h3>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Upload files or fetch from secure HTTP(S) URLs
            </li>
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Fast conversion with streaming for large files
            </li>
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Process up to {maxFiles} items at once (combined files and URLs)
            </li>
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              No data stored - all processing happens securely
            </li>
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Free, no signup required
            </li>
          </ul>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && previewFile && (
        <PreviewModal
          isOpen={showPreview}
          onClose={() => setShowPreview(false)}
          data={previewFile}
        />
      )}
    </div>
  );
}

export default FileConverter;
