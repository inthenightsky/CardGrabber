import argparse
import asyncio
import csv
import logging
import os
import sys
from datetime import datetime
from typing import Tuple, List

from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"acegrading_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default constants
DEFAULT_INPUT_FILE: str = "certs.txt"
DEFAULT_CONCURRENCY: int = 5
DEFAULT_TIMEOUT: int = 15000
DEFAULT_RETRY_COUNT: int = 3
DEFAULT_RETRY_DELAY: float = 2.0
DEFAULT_RATE_LIMIT: float = 1.0

async def create_stealth_page(context: BrowserContext) -> Page:
    page = await context.new_page()
    await stealth_async(page)
    return page

async def fetch_certificate_data(
    context: BrowserContext,
    certificate_id: str,
    timeout: int = DEFAULT_TIMEOUT,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: float = DEFAULT_RETRY_DELAY
) -> tuple[str, str, str] | None:
    url = f"https://acegrading.com/cert/{certificate_id}"

    for attempt in range(1, retry_count + 2):
        page = await create_stealth_page(context)
        try:
            if attempt > 1:
                logger.info(f"Retrying certificate {certificate_id}, attempt {attempt}/{retry_count+1}")
                await asyncio.sleep(retry_delay * attempt)

            logger.debug(f"Fetching certificate {certificate_id}")
            await page.goto(url, timeout=timeout)
            await asyncio.sleep(1.5)

            await page.wait_for_selector("//h2[contains(@class, 'sm:text-2xl')]")

            card_name_locator = page.locator("//h2[contains(@class, 'sm:text-2xl')]")
            card_name_raw = await card_name_locator.first.text_content()
            card_name: str = " ".join(card_name_raw.split())

            grade_locator = page.locator("//div[contains(@class, 'w-3/4') and contains(@class, 'bg-gold')]")
            grade_raw = await grade_locator.first.text_content()
            grade: str = grade_raw.strip()

            logger.debug(f"Fetched certificate {certificate_id}: {card_name} - {grade}")
            await page.close()
            return certificate_id, card_name, grade

        except PlaywrightTimeoutError:
            logger.warning(f"Timeout for certificate {certificate_id} on attempt {attempt}")
        except Exception as error:
            logger.error(f"Error fetching certificate {certificate_id}: {error}")
        finally:
            await page.close()

    await save_debug_snapshot(context, certificate_id, timeout=timeout)
    return certificate_id, "Error", "Error"

async def save_debug_snapshot(context: BrowserContext, certificate_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    page = await create_stealth_page(context)
    debug_dir = "debug_snapshots"
    os.makedirs(debug_dir, exist_ok=True)
    file_path = os.path.join(debug_dir, f"{certificate_id}.html")
    try:
        await page.goto(f"https://acegrading.com/cert/{certificate_id}", timeout=timeout)
        await asyncio.sleep(2)
        content = await page.content()
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Saved debug snapshot for certificate {certificate_id}")
    except Exception as error:
        logger.error(f"Failed to save snapshot for certificate {certificate_id}: {error}")
    finally:
        await page.close()

async def process_certificate_batch(
    context: BrowserContext,
    certificate_ids: List[str],
    timeout: int = DEFAULT_TIMEOUT,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    rate_limit: float = DEFAULT_RATE_LIMIT
) -> List[Tuple[str, str, str]]:
    tasks = []
    for index, certificate_id in enumerate(certificate_ids):
        if index > 0 and rate_limit > 0:
            await asyncio.sleep(rate_limit)
        tasks.append(fetch_certificate_data(
            context,
            certificate_id,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay
        ))
    return await asyncio.gather(*tasks)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch card information from ACE Grading's certification database.")
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT_FILE, help="Input file path")
    parser.add_argument("-o", "--output", help="Output CSV file path")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Number of concurrent fetches")
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in milliseconds")
    parser.add_argument("-r", "--retries", type=int, default=DEFAULT_RETRY_COUNT, help="Number of retries on failure")
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_RETRY_DELAY, help="Delay between retries in seconds")
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT, help="Rate limit between requests in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()

async def main() -> None:
    args = parse_arguments()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    output_file: str = args.output or f"cert_lookup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    try:
        with open(args.input, "r") as file:
            certificate_ids = [line.strip() for line in file if line.strip()]
    except Exception as error:
        logger.error(f"Failed to read input file: {error}")
        sys.exit(1)

    if not certificate_ids:
        logger.error("No certificate IDs found.")
        sys.exit(1)

    logger.info(f"Loaded {len(certificate_ids)} certificate IDs")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()

        all_results: List[Tuple[str, str, str]] = []

        with tqdm(total=len(certificate_ids), desc="Processing certificates") as progress_bar:
            for i in range(0, len(certificate_ids), args.concurrency):
                batch = certificate_ids[i:i + args.concurrency]
                results = await process_certificate_batch(
                    context,
                    batch,
                    timeout=args.timeout,
                    retry_count=args.retries,
                    retry_delay=args.delay,
                    rate_limit=args.rate_limit
                )
                all_results.extend(results)
                progress_bar.update(len(batch))

        await browser.close()

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Certificate ID", "Card Name", "Grade"])
            writer.writerows(all_results)
        logger.info(f"Saved results to {output_file}")
    except Exception as error:
        logger.error(f"Failed to write output file: {error}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as error:
        logger.error(f"Fatal error: {error}")
        sys.exit(1)
