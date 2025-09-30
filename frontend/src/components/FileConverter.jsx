import { useState, useRef } from 'react';
import { 
  ArrowUpTrayIcon, 
  DocumentArrowDownIcon,
  XMarkIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import axios from 'axios';
import ReactGA from 'react-ga4';
import PreviewModal from './PreviewModal';

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
  const [isDragging, setIsDragging] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState(null);
  const [previewFile, setPreviewFile] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);

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
    
    if (files.length + newFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`);
      return;
    }

    // Filter by accepted formats
    const validFiles = newFiles.filter(file => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      return acceptedFormats.includes(ext);
    });

    if (validFiles.length !== newFiles.length) {
      setError(`Only ${acceptedFormats.join(', ')} files are accepted`);
    }

    setFiles(prev => [...prev, ...validFiles]);

    // Track file upload
    ReactGA.event({
      category: 'Conversion',
      action: 'File Uploaded',
      label: title,
      value: validFiles.length,
    });
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handlePreview = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/v1/preview`, formData);
      setPreviewFile({ name: file.name, data: response.data });
      setShowPreview(true);

      ReactGA.event({
        category: 'Conversion',
        action: 'File Previewed',
        label: title,
      });
    } catch (err) {
      console.error('Preview failed:', err);
      setError('Failed to preview file. Please try again.');
    }
  };

  const handleConvert = async () => {
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setIsConverting(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Determine filename and extension
      let filename;
      if (files.length === 1) {
        const originalName = files[0].name.split('.').slice(0, -1).join('.');
        filename = `${originalName}${outputFormat}`;
      } else {
        filename = `converted_files.zip`;
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      // Track conversion
      ReactGA.event({
        category: 'Conversion',
        action: 'File Converted',
        label: title,
        value: files.length,
      });

      // Track download
      ReactGA.event({
        category: 'Conversion',
        action: 'File Downloaded',
        label: title,
        value: files.length,
      });

      // Clear files after successful conversion
      setFiles([]);
    } catch (err) {
      console.error('Conversion failed:', err);
      setError(err.response?.data?.detail?.message || 'Conversion failed. Please try again.');
      
      ReactGA.event({
        category: 'Conversion',
        action: 'Conversion Failed',
        label: title,
      });
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
            Accepted formats: {acceptedFormats.join(', ')} • Max {maxFiles} files • Up to 500MB each
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
              Selected Files ({files.length}/{maxFiles})
            </h3>
            {files.map((file, index) => (
              <div
                key={index}
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
                      handlePreview(file);
                    }}
                    className="p-2 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded transition-colors"
                    title="Preview"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Convert Button */}
        {files.length > 0 && (
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
              `Convert to ${outputFormat.replace('.', '').toUpperCase()}`
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
              Fast conversion with streaming for large files
            </li>
            <li className="flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Process up to {maxFiles} files at once
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