# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please open a GitHub issue for any security concerns. Do not include PHI or real patient data in any report.

## Security Design

- RadScan Lite never persists uploaded files to disk after a session ends
- No network requests are made by the scanner
- ZIP path traversal is explicitly prevented
- Compression ratio limits protect against ZIP bomb attacks
- Uploaded content is never executed
- PHI values are never displayed in the UI, logs, or exported reports
- Temporary directories are cleaned up after each session
