# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Use GitHub private vulnerability reporting when available. If it is not available, open a minimal public issue that does not include PHI, real DICOM files, credentials, private paths, or institutional details.

## Security Design

- RadScan Lite never persists uploaded files to disk after a session ends
- No network requests are made by the scanner
- ZIP path traversal is explicitly prevented
- Compression ratio limits protect against ZIP bomb attacks
- Uploaded content is never executed
- PHI values are never displayed in the UI, logs, or exported reports
- Temporary directories are cleaned up after each session
