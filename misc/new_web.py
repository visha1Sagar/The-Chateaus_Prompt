import asyncio
import json
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from urllib.parse import urljoin, urlparse
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


# Define your markdown generator.
md_generator = DefaultMarkdownGenerator(
    options={
        "ignore_links": True,
        "ignore_images": True,
        "escape_html": False,
        # "skip_internal_links": True,
        # "body_width": 80
    }
)

# # Create a run configuration.
run_config = CrawlerRunConfig(
    markdown_generator=md_generator,
    cache_mode=CacheMode.BYPASS,
)

def remove_images(markdown_text: str) -> str:
    """Remove markdown image syntax (e.g. ![alt](url)) from the text."""
    return re.sub(r'!\[.*?\]\(.*?\)', '', markdown_text)

async def crawl_page(crawler, url, base_domain, depth, max_depth, visited, pages_data):
    if url in visited:
        return None
    visited.add(url)
    try:
        result = await crawler.arun(url=url, config=run_config)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


    # cleaned_markdown = remove_images(result.markdown)
    print(f"\nFetched content from: {url}")
    # print(cleaned_markdown[:200])  # Preview first 200 characters
    print(result.cleaned_html[:200])

    # Extract child URLs only if we haven't reached max_depth.
    child_urls = set()
    if depth < max_depth:
        for link in result.links.get("internal", []):
            full_url = urljoin(url, link["href"])
            if urlparse(full_url).netloc == base_domain and full_url not in visited:
                child_urls.add(full_url)

    # Store the page details in the dictionary.
    pages_data[url] = {
        "markdown": result.markdown_v2.raw_markdown,
        "child_urls": list(child_urls)
    }

    # Recursively crawl each child URL.
    if depth < max_depth:
        tasks = [
            crawl_page(crawler, child_url, base_domain, depth + 1, max_depth, visited, pages_data)
            for child_url in child_urls
        ]
        await asyncio.gather(*tasks)
    
    return url

async def call_crawler(start_url: str = "https://nust.edu.pk", output_file: str = "crawl_results.json",):
    # start_url = "https://visionrdai.com/"
    base_domain = urlparse(start_url).netloc
    visited = set()
    pages_data = {}  # This will map each URL to its details.

    # Pass your browser config using the 'browser_config' keyword and run config via config parameter.
    async with AsyncWebCrawler() as crawler:
        print("Browser should launch now...")
        # Set max_depth to 2 (or 3, as desired) for the recursive crawl.
        await crawl_page(crawler, start_url, base_domain, depth=0, max_depth=3, visited=visited, pages_data=pages_data)
    
    # Final output structure: a root URL and a dictionary of pages.
    final_output = {
        "root": start_url,
        "pages": pages_data
    }
    
    # Save the JSON to a file for later analysis.
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    print(f"Crawl data saved to {output_file}")
    
    return output_file

if __name__ == "__main__":
    # asyncio.run(main("https://visionrdai.com/"))
    asyncio.run(call_crawler())
