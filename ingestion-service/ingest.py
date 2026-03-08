#!/usr/bin/env python3
"""
Local RAG Ingestion Service
Processes documents from various sources (GitHub, S3, URLs) and stores them in vector databases.
Supports recursive web crawling for comprehensive HTML content extraction.
"""

import os
import sys
import time
import yaml
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Union
import logging
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json
import base64

from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Document as LlamaStackDocument

# Import docling for document processing
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.labels import DocItemLabel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Confluence API client for accessing Confluence pages and spaces."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None, 
                 token: str = None, api_token: str = None):
        """
        Initialize Confluence client.
        
        Args:
            base_url: Confluence base URL (e.g., https://company.atlassian.net)
            username: Username for basic auth
            password: Password for basic auth  
            token: Personal Access Token
            api_token: API token for Atlassian Cloud
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/rest/api"
        self.session = requests.Session()
        
        # Setup authentication
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        elif api_token and username:
            # Atlassian Cloud API token
            auth_string = f"{username}:{api_token}"
            b64_auth = base64.b64encode(auth_string.encode()).decode()
            self.session.headers.update({'Authorization': f'Basic {b64_auth}'})
        elif username and password:
            self.session.auth = (username, password)
        else:
            logger.warning("No Confluence authentication provided - only public pages accessible")
    
    def get_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get Confluence page content by ID."""
        try:
            url = f"{self.api_base}/content/{page_id}"
            params = {
                'expand': 'body.storage,space,version,ancestors'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching Confluence page {page_id}: {e}")
            return None
    
    def get_page_by_title(self, space_key: str, title: str) -> Optional[Dict[str, Any]]:
        """Get Confluence page by space and title."""
        try:
            url = f"{self.api_base}/content"
            params = {
                'type': 'page',
                'spaceKey': space_key,
                'title': title,
                'expand': 'body.storage,space,version'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                return data['results'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Confluence page '{title}' in space '{space_key}': {e}")
            return None
    
    def get_space_pages(self, space_key: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Get all pages in a Confluence space."""
        try:
            pages = []
            start = 0
            
            while len(pages) < limit:
                url = f"{self.api_base}/content"
                params = {
                    'type': 'page',
                    'spaceKey': space_key,
                    'expand': 'body.storage,space,version',
                    'limit': min(50, limit - len(pages)),
                    'start': start
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if not data['results']:
                    break
                    
                pages.extend(data['results'])
                start += len(data['results'])
                
                # Check if we've reached the end
                if len(data['results']) < params['limit']:
                    break
            
            return pages[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching pages from Confluence space '{space_key}': {e}")
            return []
    
    def extract_page_id_from_url(self, url: str) -> Optional[str]:
        """Extract page ID from various Confluence URL formats."""
        try:
            parsed = urlparse(url)
            
            # Standard page URL: /spaces/SPACE/pages/123456/Page+Title
            if '/pages/' in parsed.path:
                parts = parsed.path.split('/pages/')
                if len(parts) > 1:
                    page_part = parts[1].split('/')[0]
                    if page_part.isdigit():
                        return page_part
            
            # Direct page URL: /display/SPACE/Page+Title
            if '/display/' in parsed.path:
                # We'll need to resolve this via API using space and title
                parts = parsed.path.split('/display/')
                if len(parts) > 1:
                    path_parts = parts[1].split('/', 1)
                    if len(path_parts) == 2:
                        space_key = path_parts[0]
                        title = path_parts[1].replace('+', ' ')
                        page_data = self.get_page_by_title(space_key, title)
                        return page_data['id'] if page_data else None
            
            # Query parameter: ?pageId=123456
            if parsed.query:
                query_params = parse_qs(parsed.query)
                if 'pageId' in query_params:
                    return query_params['pageId'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting page ID from Confluence URL {url}: {e}")
            return None
    
    def is_confluence_url(self, url: str) -> bool:
        """Check if URL is a Confluence page."""
        try:
            parsed = urlparse(url)
            confluence_indicators = [
                '/wiki/',
                '/display/',
                '/spaces/',
                '/pages/',
                'confluence' in parsed.netloc.lower(),
                'atlassian.net' in parsed.netloc.lower()
            ]
            
            return any(indicator in url.lower() for indicator in confluence_indicators)
            
        except Exception:
            return False
    
    def convert_storage_to_text(self, storage_content: str) -> str:
        """Convert Confluence storage format to plain text."""
        try:
            # Parse the storage format (XML-like)
            soup = BeautifulSoup(storage_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['ac:structured-macro', 'ac:parameter']):
                element.decompose()
            
            # Extract text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up extra whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error converting Confluence storage format: {e}")
            return storage_content


class WebCrawler:
    """Web crawler for recursive HTML link extraction and processing with Confluence support."""
    
    def __init__(self, max_depth: int = 2, same_domain_only: bool = True, 
                 max_pages: int = 50, delay: float = 1.0, confluence_config: Dict = None):
        """
        Initialize the web crawler.
        
        Args:
            max_depth: Maximum crawling depth (default: 2)
            same_domain_only: Only crawl within the same domain (default: True)
            max_pages: Maximum number of pages to crawl (default: 50)
            delay: Delay between requests in seconds (default: 1.0)
            confluence_config: Confluence authentication config (optional)
        """
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.max_pages = max_pages
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.discovered_urls: List[str] = []
        
        # Initialize Confluence client if config provided
        self.confluence_client = None
        if confluence_config:
            self.confluence_client = ConfluenceClient(
                base_url=confluence_config.get('base_url'),
                username=confluence_config.get('username'),
                password=confluence_config.get('password'),
                token=confluence_config.get('token'),
                api_token=confluence_config.get('api_token')
            )
        
    def is_valid_url(self, url: str, base_domain: str = None) -> bool:
        """Check if URL is valid for crawling."""
        try:
            parsed = urlparse(url)
            
            # Must be HTTP/HTTPS
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Skip fragments and empty paths that just redirect
            if parsed.fragment and not parsed.path:
                return False
                
            # Skip common non-content files
            skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
                             '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot',
                             '.zip', '.tar', '.gz', '.exe', '.dmg', '.pdf'}
            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            # Domain restriction
            if self.same_domain_only and base_domain:
                if parsed.netloc.lower() != base_domain.lower():
                    return False
                    
            return True
            
        except Exception as e:
            logger.debug(f"Invalid URL {url}: {e}")
            return False
    
    def extract_links(self, url: str, html_content: str, base_domain: str) -> List[str]:
        """Extract all valid links from HTML content, including Confluence links."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if not href or href.startswith('#'):
                    continue
                    
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                
                # Clean URL (remove fragments for deduplication)
                clean_url = absolute_url.split('#')[0]
                
                # Special handling for Confluence links
                if self.confluence_client and self.confluence_client.is_confluence_url(clean_url):
                    links.append(clean_url)
                elif self.is_valid_url(clean_url, base_domain):
                    links.append(clean_url)
                    
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    def fetch_confluence_content(self, url: str) -> Optional[str]:
        """Fetch content from Confluence URL."""
        if not self.confluence_client:
            logger.warning(f"Confluence client not configured, cannot fetch: {url}")
            return None
            
        try:
            page_id = self.confluence_client.extract_page_id_from_url(url)
            if not page_id:
                logger.warning(f"Could not extract page ID from Confluence URL: {url}")
                return None
                
            page_data = self.confluence_client.get_page_content(page_id)
            if not page_data:
                return None
                
            # Extract content from storage format
            body = page_data.get('body', {}).get('storage', {})
            if body and 'value' in body:
                content = self.confluence_client.convert_storage_to_text(body['value'])
                
                # Add metadata as text
                title = page_data.get('title', '')
                space_name = page_data.get('space', {}).get('name', '')
                
                full_content = f"Title: {title}\n"
                if space_name:
                    full_content += f"Space: {space_name}\n"
                full_content += f"URL: {url}\n\n{content}"
                
                return full_content
                
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Confluence content from {url}: {e}")
            return None
    
    def crawl_recursive(self, root_urls: List[str]) -> List[str]:
        """
        Recursively crawl websites starting from root URLs.
        
        Args:
            root_urls: List of starting URLs to crawl
            
        Returns:
            List of all discovered URLs (including root URLs)
        """
        logger.info(f"Starting recursive crawl of {len(root_urls)} root URLs")
        
        # Initialize with root URLs
        to_crawl = [(url, 0) for url in root_urls]  # (url, depth)
        self.discovered_urls.extend(root_urls)
        
        while to_crawl and len(self.discovered_urls) < self.max_pages:
            current_url, depth = to_crawl.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
                
            # Skip if max depth exceeded
            if depth > self.max_depth:
                continue
                
            logger.info(f"Crawling: {current_url} (depth: {depth})")
            
            try:
                # Check if this is a Confluence URL and handle specially
                if self.confluence_client and self.confluence_client.is_confluence_url(current_url):
                    logger.info(f"Processing Confluence page: {current_url}")
                    
                    # For Confluence pages, we don't need to fetch HTML - use API instead
                    confluence_content = self.fetch_confluence_content(current_url)
                    if confluence_content:
                        # For Confluence pages, we might want to extract linked pages
                        if depth < self.max_depth:
                            # Try to get related pages or space pages
                            page_id = self.confluence_client.extract_page_id_from_url(current_url)
                            if page_id:
                                page_data = self.confluence_client.get_page_content(page_id)
                                if page_data and 'space' in page_data:
                                    space_key = page_data['space']['key']
                                    # Get other pages in the same space (limited)
                                    space_pages = self.confluence_client.get_space_pages(space_key, limit=10)
                                    for page in space_pages:
                                        page_url = f"{self.confluence_client.base_url}/spaces/{space_key}/pages/{page['id']}"
                                        if page_url not in self.visited_urls and page_url not in self.discovered_urls:
                                            to_crawl.append((page_url, depth + 1))
                                            self.discovered_urls.append(page_url)
                                            logger.debug(f"  Found Confluence page: {page_url}")
                    
                    self.visited_urls.add(current_url)
                    
                else:
                    # Regular HTML page processing
                    response = requests.get(current_url, timeout=30)
                    response.raise_for_status()
                    
                    # Only process HTML content
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        logger.debug(f"Skipping non-HTML content: {current_url}")
                        self.visited_urls.add(current_url)
                        continue
                    
                    # Extract domain for filtering
                    base_domain = urlparse(current_url).netloc
                    
                    # Extract links if not at max depth
                    if depth < self.max_depth:
                        links = self.extract_links(current_url, response.text, base_domain)
                        
                        # Add new links to crawl queue
                        for link in links:
                            if link not in self.visited_urls and link not in self.discovered_urls:
                                to_crawl.append((link, depth + 1))
                                self.discovered_urls.append(link)
                                logger.debug(f"  Found link: {link}")
                    
                    self.visited_urls.add(current_url)
                
                # Rate limiting
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Error crawling {current_url}: {e}")
                self.visited_urls.add(current_url)
        
        logger.info(f"Crawl completed. Found {len(self.discovered_urls)} total URLs")
        return self.discovered_urls


class IngestionService:
    """Service for ingesting documents into vector databases."""
    
    def __init__(self, config_path: str):
        """Initialize the ingestion service with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Llama Stack client
        self.llama_stack_url = self.config['llamastack']['base_url']
        self.client = None
        
        # Vector DB configuration
        self.vector_db_config = self.config['vector_db']
        
        # Document converter setup - support both PDF and HTML
        pdf_pipeline_options = PdfPipelineOptions()
        pdf_pipeline_options.generate_picture_images = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options),
                InputFormat.HTML: {},  # HTML format support
                InputFormat.DOCX: {},  # Word documents
                InputFormat.PPTX: {},  # PowerPoint presentations
            }
        )
        self.chunker = HybridChunker()
    
    def wait_for_llamastack(self, max_retries: int = 30, retry_delay: int = 5):
        """Wait for Llama Stack to be ready."""
        logger.info(f"Waiting for Llama Stack at {self.llama_stack_url}...")
        
        for attempt in range(max_retries):
            try:
                self.client = LlamaStackClient(base_url=self.llama_stack_url)
                # Try to list models as a health check
                self.client.models.list()
                logger.info("Llama Stack is ready!")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Attempt {attempt + 1}/{max_retries}: Llama Stack not ready yet. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Llama Stack after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def fetch_from_github(self, config: Dict[str, Any], temp_dir: str) -> List[str]:
        """Fetch documents from a GitHub repository. Supports PDF, HTML, DOCX, PPTX."""
        url = config['url']
        path = config.get('path', '')
        branch = config.get('branch', 'main')
        token = config.get('token', '')
        
        logger.info(f"Cloning from GitHub: {url} (branch: {branch}, path: {path})")
        
        clone_dir = os.path.join(temp_dir, 'repo')
        
        # Prepare git clone command
        if token:
            # Insert token into URL for private repos
            auth_url = url.replace('https://', f'https://{token}@')
            cmd = ['git', 'clone', '--depth', '1', '--branch', branch, auth_url, clone_dir]
        else:
            cmd = ['git', 'clone', '--depth', '1', '--branch', branch, url, clone_dir]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            return []
        
        # Get the target directory
        target_dir = os.path.join(clone_dir, path) if path else clone_dir
        
        if not os.path.exists(target_dir):
            logger.error(f"Path {path} not found in repository")
            return []
        
        # Find all supported document files
        supported_extensions = ('.pdf', '.html', '.htm', '.docx', '.pptx')
        document_files = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    document_files.append(os.path.join(root, file))
        
        logger.info(f"Found {len(document_files)} document files in {target_dir}")
        return document_files
    
    def fetch_from_s3(self, config: Dict[str, Any], temp_dir: str) -> List[str]:
        """Fetch documents from S3/MinIO. Supports PDF, HTML, DOCX, PPTX."""
        import boto3
        
        endpoint = config['endpoint']
        bucket = config['bucket']
        access_key = config['access_key']
        secret_key = config['secret_key']
        prefix = config.get('prefix', '')
        
        logger.info(f"Fetching from S3: {endpoint}/{bucket}")
        
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=False
        )
        
        download_dir = os.path.join(temp_dir, 's3_files')
        os.makedirs(download_dir, exist_ok=True)
        
        # List and download objects
        supported_extensions = ('.pdf', '.html', '.htm', '.docx', '.pptx')
        document_files = []
        try:
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key.lower().endswith(supported_extensions):
                        file_path = os.path.join(download_dir, os.path.basename(key))
                        logger.info(f"Downloading: {key}")
                        s3.download_file(bucket, key, file_path)
                        document_files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error fetching from S3: {e}")
            return []
        
        logger.info(f"Downloaded {len(document_files)} document files from S3")
        return document_files
    
    def fetch_from_urls(self, config: Dict[str, Any], temp_dir: str) -> List[str]:
        """
        Fetch documents from direct URLs - supports PDF, HTML, DOCX, PPTX.
        Includes recursive web crawling for comprehensive HTML content extraction.
        """
        urls = config.get('urls', [])
        crawl_config = config.get('crawl', {})
        
        # Crawling configuration
        enable_crawling = crawl_config.get('enabled', False)
        max_depth = crawl_config.get('max_depth', 2)
        same_domain_only = crawl_config.get('same_domain_only', True)
        max_pages = crawl_config.get('max_pages', 50)
        crawl_delay = crawl_config.get('delay', 1.0)
        
        logger.info(f"Processing {len(urls)} base URLs (crawling: {'enabled' if enable_crawling else 'disabled'})")
        
        # If crawling is enabled, use web crawler
        if enable_crawling:
            # Get Confluence configuration if available
            confluence_config = crawl_config.get('confluence', {})
            
            crawler = WebCrawler(
                max_depth=max_depth,
                same_domain_only=same_domain_only,
                max_pages=max_pages,
                delay=crawl_delay,
                confluence_config=confluence_config if confluence_config else None
            )
            
            # Store crawler reference for document processing
            self.crawler = crawler
            
            # Separate HTML URLs for crawling vs direct document URLs
            html_urls = []
            direct_urls = []
            
            for url in urls:
                if url.lower().endswith(('.pdf', '.docx', '.pptx')):
                    direct_urls.append(url)
                else:
                    html_urls.append(url)  # Assume HTML for crawling
            
            # Crawl HTML URLs recursively
            if html_urls:
                logger.info(f"Starting recursive crawl from {len(html_urls)} root URLs")
                crawled_urls = crawler.crawl_recursive(html_urls)
                all_urls = direct_urls + crawled_urls
            else:
                all_urls = direct_urls
                
        else:
            # No crawling - process URLs directly
            all_urls = urls
        
        # Validate and filter URLs
        supported_formats = ['.pdf', '.html', '.htm', '.docx', '.pptx']
        valid_urls = []
        
        for url in all_urls:
            try:
                # Basic URL validation
                if url.startswith(('http://', 'https://')):
                    # Check if URL appears to point to a supported format
                    url_lower = url.lower()
                    is_supported = (
                        any(url_lower.endswith(fmt) for fmt in supported_formats) or
                        'html' in url_lower or  # HTML pages without .html extension
                        url_lower.endswith('/') or  # Directory URLs (likely HTML)
                        '?' in url or  # URLs with parameters (often dynamic HTML)
                        '#' in url or  # URLs with fragments (HTML pages)
                        not any(url_lower.endswith(ext) for ext in ['.jpg', '.png', '.css', '.js'])  # Exclude obvious non-documents
                    )
                    
                    if is_supported:
                        valid_urls.append(url)
                        if enable_crawling and url not in urls:
                            logger.debug(f"Added crawled URL: {url}")
                        else:
                            logger.info(f"Added direct URL: {url}")
                    else:
                        logger.debug(f"Skipped unsupported URL: {url}")
                else:
                    logger.warning(f"Invalid URL format: {url}")
            except Exception as e:
                logger.error(f"Error validating URL {url}: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in valid_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Prepared {len(unique_urls)} URLs for processing ({len(unique_urls) - len(urls)} discovered via crawling)")
        return unique_urls
    
    def process_documents(self, sources: List[str]) -> List[LlamaStackDocument]:
        """Process documents (files or URLs) into chunks using docling or direct processing."""
        logger.info(f"Processing {len(sources)} documents with docling and Confluence integration...")
        
        llama_documents = []
        doc_id = 0
        
        for source in sources:
            try:
                # Determine source type and display name
                if source.startswith(('http://', 'https://')):
                    source_name = source.split('/')[-1] or source
                    logger.info(f"Processing URL: {source_name}")
                else:
                    source_name = os.path.basename(source)
                    logger.info(f"Processing file: {source_name}")
                
                # Check if this is a Confluence URL that we've already processed
                if hasattr(self, 'crawler') and self.crawler and \
                   self.crawler.confluence_client and \
                   self.crawler.confluence_client.is_confluence_url(source):
                    
                    # Fetch Confluence content directly
                    logger.info(f"Processing Confluence page: {source}")
                    confluence_content = self.crawler.fetch_confluence_content(source)
                    
                    if confluence_content:
                        # Manual chunking for Confluence content
                        chunk_size = 512  # tokens, approximate by words
                        words = confluence_content.split()
                        
                        # Simple chunking by word count (approximate token count)
                        for i in range(0, len(words), chunk_size):
                            chunk_words = words[i:i + chunk_size]
                            if len(chunk_words) > 10:  # Only meaningful chunks
                                doc_id += 1
                                chunk_text = ' '.join(chunk_words)
                                
                                llama_documents.append(
                                    LlamaStackDocument(
                                        document_id=f"confluence-{doc_id}",
                                        content=chunk_text,
                                        mime_type="text/plain",
                                        metadata={
                                            "source": source,
                                            "type": "confluence",
                                            "source_name": source_name
                                        },
                                    )
                                )
                        
                        logger.info(f"  → Created {len([d for d in llama_documents if d.metadata.get('source') == source])} Confluence chunks")
                    else:
                        logger.warning(f"Could not fetch Confluence content from: {source}")
                
                else:
                    # Use Docling for regular documents (PDF, HTML, DOCX, PPTX, etc.)
                    docling_doc = self.converter.convert(source=source).document
                    chunks = self.chunker.chunk(docling_doc)
                    chunk_count = 0
                    
                    # Extract text chunks
                    for chunk in chunks:
                        if any(
                            c.label in [DocItemLabel.TEXT, DocItemLabel.PARAGRAPH]
                            for c in chunk.meta.doc_items
                        ):
                            doc_id += 1
                            chunk_count += 1
                            llama_documents.append(
                                LlamaStackDocument(
                                    document_id=f"doc-{doc_id}",
                                    content=chunk.text,
                                    mime_type="text/plain",
                                    metadata={"source": source_name, "type": "document"},
                                )
                            )
                    
                    logger.info(f"  → Created {chunk_count} document chunks")
            
            except Exception as e:
                logger.error(f"Error processing {source}: {e}")
        
        logger.info(f"Total chunks created: {len(llama_documents)}")
        return llama_documents

    def get_provider_id(self) -> str:
        """Get the provider ID for the vector database."""
        providers = self.client.providers.list()
        for provider in providers:
            if provider.api == "vector_io":
                return provider.provider_id
        return None
    
    def create_vector_db(self, vector_store_name: str, documents: List[LlamaStackDocument]) -> bool:
        """Create vector database and insert documents."""
        if not documents:
            logger.warning(f"No documents to insert for {vector_store_name}")
            return False
        
        logger.info(f"Creating vector database: {vector_store_name}")
        
        # Register vector database
        try:
            self.client.vector_dbs.register(
                vector_db_id=vector_store_name,
                embedding_model=self.vector_db_config['embedding_model'],
                embedding_dimension=self.vector_db_config['embedding_dimension'],
               # provider_id=self.vector_db_config['provider_id'] or self.get_provider_id(),
               provider_id=self.get_provider_id(),
            )
            logger.info(f"Vector DB '{vector_store_name}' registered successfully")
        
        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg.lower():
                logger.info(f"Vector DB '{vector_store_name}' already exists, continuing...")
            else:
                logger.error(f"Failed to register vector DB '{vector_store_name}': {e}")
                return False
        
        # Insert documents
        try:
            logger.info(f"Inserting {len(documents)} chunks into vector database...")
            self.client.tool_runtime.rag_tool.insert(
                documents=documents,
                vector_db_id=vector_store_name,
                chunk_size_in_tokens=self.vector_db_config['chunk_size_in_tokens'],
            )
            logger.info(f"✓ Successfully inserted documents into '{vector_store_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Error inserting documents into '{vector_store_name}': {e}")
            return False
    
    def process_pipeline(self, pipeline_name: str, pipeline_config: Dict[str, Any]) -> bool:
        """Process a single pipeline."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing pipeline: {pipeline_name}")
        logger.info(f"{'='*60}")
        
        if not pipeline_config.get('enabled', False):
            logger.info(f"Pipeline '{pipeline_name}' is disabled, skipping")
            return True
        
        vector_store_name = pipeline_config['vector_store_name']
        source = pipeline_config['source']
        source_config = pipeline_config['config']
        
        # Create temporary directory for this pipeline
        with tempfile.TemporaryDirectory() as temp_dir:
            # Fetch documents based on source type
            if source == 'GITHUB':
                document_sources = self.fetch_from_github(source_config, temp_dir)
            elif source == 'S3':
                document_sources = self.fetch_from_s3(source_config, temp_dir)
            elif source == 'URL':
                document_sources = self.fetch_from_urls(source_config, temp_dir)
            else:
                logger.error(f"Unknown source type: {source}")
                return False
            
            if not document_sources:
                logger.warning(f"No documents found for pipeline '{pipeline_name}'")
                return False
            
            # Process documents
            documents = self.process_documents(document_sources)
            
            if not documents:
                logger.warning(f"No documents processed for pipeline '{pipeline_name}'")
                return False
            
            # Create vector database and insert documents
            return self.create_vector_db(vector_store_name, documents)
    
    def run(self):
        """Run the ingestion service."""
        logger.info("Starting RAG Ingestion Service")
        logger.info(f"Configuration: {os.path.abspath('ingestion-config.yaml')}")
        
        # Wait for Llama Stack to be ready
        if not self.wait_for_llamastack():
            logger.error("Failed to connect to Llama Stack. Exiting.")
            sys.exit(1)
        
        # Process all enabled pipelines
        pipelines = self.config.get('pipelines', {})
        total = len(pipelines)
        successful = 0
        failed = 0
        skipped = 0
        
        for pipeline_name, pipeline_config in pipelines.items():
            if not pipeline_config.get('enabled', False):
                skipped += 1
                continue
            
            try:
                if self.process_pipeline(pipeline_name, pipeline_config):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Unexpected error processing pipeline '{pipeline_name}': {e}")
                failed += 1
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("Ingestion Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Total pipelines: {total}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"{'='*60}\n")
        
        if failed > 0:
            logger.warning(f"{failed} pipeline(s) failed. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("All pipelines completed successfully!")
            sys.exit(0)


if __name__ == '__main__':
    config_file = os.getenv('INGESTION_CONFIG', '/config/ingestion-config.yaml')
    
    if not os.path.exists(config_file):
        logger.error(f"Configuration file not found: {config_file}")
        sys.exit(1)
    
    service = IngestionService(config_file)
    service.run()

