# Card Grabber

A Python-based tool for automatically retrieving card information from ACE Grading's certification database using their public website.

## Description

This tool automates the process of fetching card details from ACE Grading's certification website. It uses Playwright with stealth capabilities to navigate through Cloudflare protection and extract card information accurately.

Key Features:
- Concurrent certificate processing
- Built-in rate limiting and retry mechanisms
- Detailed logging system
- Progress tracking with visual feedback
- Debug snapshot capabilities for troubleshooting

## Requirements

- Python 3.7+
- Required packages:
  - playwright
  - playwright-stealth
  - tqdm

## Important Notes

⚠️ **Headless Mode Not Supported**: Due to Cloudflare protections, the tool must run with a visible browser window.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/inthenightsky/CardGrabber
   cd CardGrabber
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install playwright playwright-stealth tqdm
   playwright install chromium
   ```

## Usage

1. Create a text file (default: `certs.txt`) containing certificate numbers, one per line:
   ```
   123456
   789012
   ```

2. Run the script:
   ```bash
   python script.py
   ```

## Command-Line Options

python script.py [-h] [-i INPUT] [-o OUTPUT] [-c CONCURRENCY] [-t TIMEOUT] [-r RETRIES] [-d DELAY] [--rate-limit RATE_LIMIT] [-v]


| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | `certs.txt` | Input file path |
| `-o, --output` | `cert_lookup_results_[timestamp].csv` | Output CSV file path |
| `-c, --concurrency` | 5 | Number of concurrent requests |
| `-t, --timeout` | 15000 | Page timeout in milliseconds |
| `-r, --retries` | 3 | Number of retry attempts |
| `-d, --delay` | 2.0 | Delay between retries (seconds) |
| `--rate-limit` | 1.0 | Delay between requests (seconds) |
| `-v, --verbose` | False | Enable verbose logging |

## Output Files

The script generates three types of output files:

1. **Results CSV** (`cert_lookup_results_YYYYMMDD_HHMMSS.csv`):
   ```
   Certificate ID,Card Name,Grade
   123456,Example Card Name,10
   ```

2. **Log File** (`acegrading_scraper_YYYYMMDD_HHMMSS.log`):
   - Detailed operation logs
   - Processing statistics
   - Error messages and warnings
   - Debug information (when verbose mode is enabled)

3. **Debug Snapshots** (in `debug_snapshots` directory):
   - HTML snapshots of failed requests
   - Created automatically when errors occur
   - Named using certificate numbers (e.g., `123456.html`)

## Features in Detail

### Stealth Mode
- Uses playwright-stealth to bypass anti-bot measures
- Implements realistic browser behavior
- Required for Cloudflare navigation

### Concurrent Processing
- Processes multiple certificates simultaneously
- Configurable batch size via `--concurrency`
- Built-in rate limiting between requests

### Error Recovery
- Automatic retries for failed requests
- Exponential backoff between retry attempts
- Debug snapshots for failed certificates
- Continues processing despite individual failures

### Progress Tracking
- Real-time progress bar
- Detailed logging of operations
- Summary statistics on completion

## Error Handling

The script handles several error scenarios:

1. **Certificate Not Found**
   - Recorded as "Error" in output
   - Debug snapshot saved
   - Processing continues with next certificate

2. **Network Issues**
   - Automatic retry with backoff
   - Configurable retry attempts
   - Detailed error logging

3. **Page Loading Timeout**
   - Configurable timeout period
   - Multiple retry attempts
   - Debug snapshot on final failure

## Best Practices

1. **Rate Limiting**
   - Start with default rate limit (1 second)
   - Adjust based on server response
   - Monitor for error patterns

2. **Batch Processing**
   - Use smaller batches initially
   - Increase concurrency gradually
   - Watch for timeout errors

3. **Error Monitoring**
   - Check log files regularly
   - Review debug snapshots
   - Adjust settings if needed

## License

[MIT License](LICENSE)

## Disclaimer

This tool is for personal use only. Please respect ACE Grading's website terms of service and implement appropriate rate limiting to avoid server strain.
