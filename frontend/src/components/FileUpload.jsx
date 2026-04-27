import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

/**
 * Drag-and-drop file upload component for PDF and text documents.
 */
export default function FileUpload({ onUpload, sessionId, disabled }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0 && onUpload) {
      onUpload(acceptedFiles[0], sessionId);
    }
  }, [onUpload, sessionId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024, // 20MB
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? 'active' : ''}`}
      style={{ opacity: disabled ? 0.5 : 1 }}
    >
      <input {...getInputProps()} />
      <div className="dropzone-icon">
        <Upload size={32} color="var(--accent-primary)" />
      </div>
      <div className="dropzone-text">
        {isDragActive ? (
          <span>Drop your file here...</span>
        ) : (
          <span>
            <strong>Click to upload</strong> or drag & drop a document
          </span>
        )}
      </div>
      <div className="dropzone-hint">
        PDF, TXT, or MD files up to 20MB
      </div>
    </div>
  );
}
