import logging
import os
import sys
import subprocess


from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from website_chat.settings import DOC_DIR

logger = logging.getLogger(__name__)


async def crawl_and_return_results(base_url, max_pages=200):
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False,
            max_pages=max_pages,
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(base_url, config=config)
        return results


def check_url_in_same_path(cand_url, input_url):
    input_url.replace("https://", "")
    input_url.replace("www.", "")
    input_url.replace("http://", "")
    cand_url.replace("https://", "")
    cand_url.replace("http://", "")
    cand_url.replace("www.", "")
    return cand_url.startswith(input_url)


def save_to_mds(results, base_url: str) -> list[str]:
    # save each result to a markdown file
    target_dir = DOC_DIR
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    landing_dir = f"{target_dir}/landing"
    if not os.path.exists(landing_dir):
        os.makedirs(landing_dir)
    saved_urls = []
    for result in results:
        if result.success:
            if not check_url_in_same_path(result.url, base_url):
                continue

            filename = f"{result.url.replace('/', '_')}.md"
            output_file = os.path.join(target_dir, filename)
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(result.markdown)
            if result.url == base_url:
                output_file = os.path.join(landing_dir, filename)
                with open(output_file, "w", encoding="utf-8") as file:
                    file.write(result.markdown)
            saved_urls.append(result.url)
    return list(set(saved_urls))


async def save_website_to_docs(urls: list[str], max_pages: int):
    saved_urls = []
    logging.getLogger("crawl4ai").setLevel(logging.WARNING)

    for url in urls:
        logger.info("crawling %s", url)
        try:
            crawl_results = await crawl_and_return_results(url, max_pages)
        except Exception as e:
            if "BrowserType.launch" in str(e):
                # install playwright, run `playwright install` in bash
                logger.info("Installing playwright")

                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "playwright",
                        "install",
                        "--with-deps",
                        "--force",
                        "chromium",
                    ],
                    stdout=subprocess.DEVNULL,  # Suppress standard output
                )
                crawl_results = await crawl_and_return_results(url, max_pages)
            else:
                raise e

        saved_urls = save_to_mds(crawl_results, url)
    return saved_urls
