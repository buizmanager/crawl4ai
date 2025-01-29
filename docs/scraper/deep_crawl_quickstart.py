# basic_scraper_example.py
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.traversal import (
    BFSTraversalStrategy,
    FilterChain,
    URLPatternFilter,
    ContentTypeFilter,
)
from crawl4ai.async_webcrawler import AsyncWebCrawler
import re
import time

browser_config = BrowserConfig(headless=True, viewport_width=800, viewport_height=600)

async def basic_scraper_example():
    """
    Basic example: Scrape a blog site for articles
    - Crawls only HTML pages
    - Stays within the blog section
    - Collects all results at once
    """
    # Create a simple filter chain
    filter_chain = FilterChain(
        [
            # Only crawl pages within the blog section
            URLPatternFilter("*/basic/*"),
            # Only process HTML pages
            ContentTypeFilter(["text/html"]),
        ]
    )

    # Initialize the strategy with basic configuration
    bfs_strategy = BFSTraversalStrategy(
        max_depth=2,  # Only go 2 levels deep
        filter_chain=filter_chain,
        url_scorer=None,  # Use default scoring
        process_external_links=True,
    )

    # Create the crawler and scraper
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:
        # Start scraping
        try:
            results = await crawler.adeep_crawl(
                "https://crawl4ai.com/mkdocs", strategy=bfs_strategy
            )
            # Process results
            print(f"Crawled {len(results)} pages:")
            for result in results:
                print(f"- {result.url}: {len(result.html)} bytes")

        except Exception as e:
            print(f"Error during scraping: {e}")


# advanced_scraper_example.py
import logging

from crawl4ai.traversal import (
    BFSTraversalStrategy,
    FilterChain,
    URLPatternFilter,
    ContentTypeFilter,
    DomainFilter,
    KeywordRelevanceScorer,
    PathDepthScorer,
    FreshnessScorer,
    CompositeScorer,
)


async def advanced_scraper_example():
    """
    Advanced example: Intelligent news site scraping
    - Uses all filter types
    - Implements sophisticated scoring
    - Streams results
    - Includes monitoring and logging
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("advanced_scraper")

    # Create sophisticated filter chain
    filter_chain = FilterChain(
        [
            # Domain control
            DomainFilter(
                allowed_domains=["techcrunch.com"],
                blocked_domains=["login.techcrunch.com", "legal.yahoo.com"],
            ),
            # URL patterns
            URLPatternFilter(
                [
                    "*/article/*",
                    "*/news/*",
                    "*/blog/*",
                    re.compile(r"\d{4}/\d{2}/.*"),  # Date-based URLs
                ]
            ),
            # Content types
            ContentTypeFilter(["text/html", "application/xhtml+xml"]),
        ]
    )

    # Create composite scorer
    scorer = CompositeScorer(
        [
            # Prioritize by keywords
            KeywordRelevanceScorer(
                keywords=["news", "breaking", "update", "latest"], weight=1.0
            ),
            # Prefer optimal URL structure
            PathDepthScorer(optimal_depth=3, weight=0.7),
            # Prioritize fresh content
            FreshnessScorer(weight=0.9),
        ]
    )

    # Initialize strategy with advanced configuration
    bfs_strategy = BFSTraversalStrategy(
        max_depth=2, filter_chain=filter_chain, url_scorer=scorer
    )

    # Create crawler and scraper
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:

        # Track statistics
        stats = {"processed": 0, "errors": 0, "total_size": 0}

        try:
            # Use streaming mode
            results = []
            result_generator = await crawler.adeep_crawl(
                "https://techcrunch.com",
                strategy=bfs_strategy,
                crawler_run_config=CrawlerRunConfig(
                    scraping_strategy=LXMLWebScrapingStrategy()
                ),
                stream=True,
            )
            async for result in result_generator:
                stats["processed"] += 1

                if result.success:
                    stats["total_size"] += len(result.html)
                    logger.info(
                        f"Processed at depth: {result.depth} with score: {result.score:.3f} : \n {result.url}"
                    )
                    results.append(result)
                else:
                    stats["errors"] += 1
                    logger.error(
                        f"Failed to process {result.url}: {result.error_message}"
                    )

                # Log progress regularly
                if stats["processed"] % 10 == 0:
                    logger.info(f"Progress: {stats['processed']} URLs processed")

        except Exception as e:
            logger.error(f"Scraping error: {e}")

        finally:
            # Print final statistics
            logger.info("Scraping completed:")
            logger.info(f"- URLs processed: {stats['processed']}")
            logger.info(f"- Errors: {stats['errors']}")
            logger.info(f"- Total content size: {stats['total_size'] / 1024:.2f} KB")

            # Print filter statistics
            for filter_ in filter_chain.filters:
                logger.info(f"{filter_.name} stats:")
                logger.info(f"- Passed: {filter_.stats.passed_urls}")
                logger.info(f"- Rejected: {filter_.stats.rejected_urls}")

            # Print scorer statistics
            logger.info("Scoring statistics:")
            logger.info(f"- Average score: {scorer.stats.average_score:.2f}")
            logger.info(
                f"- Score range: {scorer.stats.min_score:.2f} - {scorer.stats.max_score:.2f}"
            )


if __name__ == "__main__":
    import asyncio
    import time

    # Run basic example
    start_time = time.perf_counter()
    print("Running basic scraper example...")
    asyncio.run(basic_scraper_example())
    end_time = time.perf_counter()
    print(f"Basic scraper example completed in {end_time - start_time:.2f} seconds")

    # # Run advanced example
    print("\nRunning advanced scraper example...")
    asyncio.run(advanced_scraper_example())
