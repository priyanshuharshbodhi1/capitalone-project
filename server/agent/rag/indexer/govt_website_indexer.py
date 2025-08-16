"""
Comprehensive Government Website Indexer

Indexes all central and state government agricultural websites for schemes,
subsidies, and policies relevant to Indian farmers.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
import re
import json

@dataclass
class IndexedContent:
    url: str
    title: str
    content: str
    scheme_name: Optional[str]
    eligibility: List[str]
    subsidy_amount: Optional[str]
    application_link: Optional[str]
    documents_required: List[str]
    state: Optional[str]
    category: str  # 'central' or 'state'
    last_updated: datetime
    metadata: Dict[str, Any]

class GovtWebsiteIndexer:
    """Comprehensive indexer for all government agricultural websites"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.indexed_urls: Set[str] = set()
        
        # Central Government Sources
        self.central_govt_sources = {
            'pmkisan.gov.in': {
                'base_url': 'https://pmkisan.gov.in',
                'schemes_paths': ['/StaticPages/Benificiaries.aspx', '/StaticPages/Scheme_Guideline.aspx'],
                'priority': 'high'
            },
            'agricoop.nic.in': {
                'base_url': 'https://agricoop.nic.in',
                'schemes_paths': ['/schemes-programmes', '/division/plant-protection', '/division/seeds'],
                'priority': 'high'
            },
            'mkisan.gov.in': {
                'base_url': 'https://mkisan.gov.in',
                'schemes_paths': ['/Home/Schemes', '/Home/SubsidySchemes'],
                'priority': 'high'
            },
            'dahd.nic.in': {
                'base_url': 'https://dahd.nic.in',
                'schemes_paths': ['/schemes', '/division/animal-husbandry'],
                'priority': 'high'
            },
            'pmfby.gov.in': {
                'base_url': 'https://pmfby.gov.in',
                'schemes_paths': ['/page/scheme', '/page/calculate-premium'],
                'priority': 'high'
            },
            'krishi.gov.in': {
                'base_url': 'https://krishi.gov.in',
                'schemes_paths': ['/schemes', '/subsidy'],
                'priority': 'medium'
            },
            'fpo.gov.in': {
                'base_url': 'https://fpo.gov.in',
                'schemes_paths': ['/schemes', '/benefits'],
                'priority': 'medium'
            },
            'pmksy.gov.in': {
                'base_url': 'https://pmksy.gov.in',
                'schemes_paths': ['/microirrigation', '/accelerated-irrigation'],
                'priority': 'high'
            }
        }
        
        # State Government Sources (all states)
        self.state_govt_sources = self._get_all_state_sources()
    
    def _get_all_state_sources(self) -> Dict[str, Dict]:
        """Get all state government agricultural department websites"""
        states = [
            'andhra-pradesh', 'arunachal-pradesh', 'assam', 'bihar', 'chhattisgarh',
            'goa', 'gujarat', 'haryana', 'himachal-pradesh', 'jharkhand', 'karnataka',
            'kerala', 'madhya-pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
            'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil-nadu',
            'telangana', 'tripura', 'uttar-pradesh', 'uttarakhand', 'west-bengal',
            'delhi', 'jammu-kashmir', 'ladakh', 'puducherry', 'andaman-nicobar',
            'chandigarh', 'dadra-nagar-haveli', 'daman-diu', 'lakshadweep'
        ]
        
        state_sources = {}
        
        # State-specific agriculture department URLs
        state_agriculture_domains = {
            'andhra-pradesh': 'apagrisnet.gov.in',
            'assam': 'agri.assam.gov.in',
            'bihar': 'krishi.bih.nic.in',
            'chhattisgarh': 'agriportal.cg.nic.in',
            'gujarat': 'agri.gujarat.gov.in',
            'haryana': 'agriharyana.gov.in',
            'himachal-pradesh': 'hpagriculture.com',
            'karnataka': 'krishi.kar.nic.in',
            'kerala': 'keralaagriculture.gov.in',
            'madhya-pradesh': 'mpkrishi.mp.gov.in',
            'maharashtra': 'krishi.maharashtra.gov.in',
            'odisha': 'agriodisha.nic.in',
            'punjab': 'agri.punjab.gov.in',
            'rajasthan': 'agriculture.rajasthan.gov.in',
            'tamil-nadu': 'tn.gov.in/agriculture',
            'telangana': 'agriculture.telangana.gov.in',
            'uttar-pradesh': 'upagriculture.com',
            'west-bengal': 'wb.gov.in/agriculture'
        }
        
        for state in states:
            if state in state_agriculture_domains:
                domain = state_agriculture_domains[state]
                state_sources[state] = {
                    'base_url': f'https://{domain}',
                    'schemes_paths': ['/schemes', '/subsidies', '/farmer-welfare', '/programs'],
                    'priority': 'medium',
                    'state_name': state.replace('-', ' ').title()
                }
        
        return state_sources
    
    async def start_indexing(self) -> List[IndexedContent]:
        """Start comprehensive indexing of all government sources"""
        self.logger.info("Starting comprehensive government website indexing...")
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'GovtSchemeIndexer/1.0'}
        ) as session:
            self.session = session
            
            all_content = []
            
            # Index central government sources
            self.logger.info("Indexing central government sources...")
            central_content = await self._index_central_sources()
            all_content.extend(central_content)
            
            # Index state government sources
            self.logger.info("Indexing state government sources...")
            state_content = await self._index_state_sources()
            all_content.extend(state_content)
            
            self.logger.info(f"Indexing completed. Total content indexed: {len(all_content)}")
            return all_content
    
    async def _index_central_sources(self) -> List[IndexedContent]:
        """Index all central government agricultural websites"""
        tasks = []
        
        for source_name, config in self.central_govt_sources.items():
            for path in config['schemes_paths']:
                url = urljoin(config['base_url'], path)
                task = self._index_single_page(url, 'central', source_name)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        content = []
        
        for result in results:
            if isinstance(result, list):
                content.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error indexing page: {result}")
        
        return content
    
    async def _index_state_sources(self) -> List[IndexedContent]:
        """Index all state government agricultural websites"""
        tasks = []
        
        for state, config in self.state_govt_sources.items():
            for path in config['schemes_paths']:
                url = urljoin(config['base_url'], path)
                task = self._index_single_page(url, 'state', state, config.get('state_name'))
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        content = []
        
        for result in results:
            if isinstance(result, list):
                content.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error indexing state page: {result}")
        
        return content
    
    async def _index_single_page(self, url: str, category: str, source: str, state_name: Optional[str] = None) -> List[IndexedContent]:
        """Index a single government webpage"""
        if url in self.indexed_urls:
            return []
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract scheme information
                schemes = self._extract_scheme_info(soup, url, category, state_name)
                
                # Also crawl linked pages for more detailed information
                linked_schemes = await self._crawl_linked_pages(soup, url, category, state_name)
                schemes.extend(linked_schemes)
                
                self.indexed_urls.add(url)
                return schemes
                
        except Exception as e:
            self.logger.error(f"Error indexing {url}: {e}")
            return []
    
    def _extract_scheme_info(self, soup: BeautifulSoup, url: str, category: str, state_name: Optional[str]) -> List[IndexedContent]:
        """Extract scheme information from webpage content"""
        schemes = []
        
        # Get page title
        title_elem = soup.find('title')
        page_title = title_elem.text.strip() if title_elem else "Government Scheme"
        
        # Extract main content
        content_areas = soup.find_all(['div', 'section', 'article'], 
                                    class_=re.compile(r'content|main|scheme|subsidy|policy', re.I))
        
        if not content_areas:
            content_areas = [soup.find('body') or soup]
        
        for content_area in content_areas:
            if not content_area:
                continue
                
            text_content = content_area.get_text(separator=' ', strip=True)
            
            # Skip if content is too short
            if len(text_content) < 100:
                continue
            
            # Extract scheme details using patterns
            scheme_info = self._parse_scheme_details(text_content, content_area)
            
            if scheme_info['scheme_name'] or any(scheme_info['eligibility']):
                schemes.append(IndexedContent(
                    url=url,
                    title=page_title,
                    content=text_content,
                    scheme_name=scheme_info['scheme_name'],
                    eligibility=scheme_info['eligibility'],
                    subsidy_amount=scheme_info['subsidy_amount'],
                    application_link=scheme_info['application_link'],
                    documents_required=scheme_info['documents_required'],
                    state=state_name,
                    category=category,
                    last_updated=datetime.now(),
                    metadata={'source_domain': urlparse(url).netloc}
                ))
        
        return schemes
    
    def _parse_scheme_details(self, text: str, content_elem) -> Dict[str, Any]:
        """Parse scheme details from text content"""
        
        # Extract scheme name
        scheme_patterns = [
            r'(?:scheme|yojana|programme|program):\s*([^.\n]+)',
            r'([A-Z][^.\n]*(?:scheme|yojana|programme|program)[^.\n]*)',
            r'(?:under|through)\s+([^.\n]*(?:scheme|yojana|programme|program)[^.\n]*)'
        ]
        
        scheme_name = None
        for pattern in scheme_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                scheme_name = match.group(1).strip()
                break
        
        # Extract eligibility criteria
        eligibility_patterns = [
            r'eligibility[:\s]*([^.\n]+)',
            r'eligible[:\s]*([^.\n]+)',
            r'(?:for|applicable to)[:\s]*([^.\n]+farmer[^.\n]*)',
            r'(?:small|marginal|large)\s+farmer[s]?',
            r'land\s+holding[:\s]*([^.\n]+)'
        ]
        
        eligibility = []
        for pattern in eligibility_patterns:
            matches = re.findall(pattern, text, re.I)
            eligibility.extend([match.strip() for match in matches if match.strip()])
        
        # Extract subsidy amount
        subsidy_patterns = [
            r'subsidy[:\s]*([^.\n]*(?:₹|rs|rupee)[^.\n]*)',
            r'(?:₹|rs\.?)\s*([0-9,]+(?:\.[0-9]+)?)[^.\n]*',
            r'([0-9]+%[^.\n]*subsidy)',
            r'up\s+to[:\s]*(₹[^.\n]+)',
            r'maximum[:\s]*(₹[^.\n]+)'
        ]
        
        subsidy_amount = None
        for pattern in subsidy_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                subsidy_amount = match.group(1).strip()
                break
        
        # Extract application link
        application_link = None
        if content_elem:
            app_links = content_elem.find_all('a', href=True, text=re.compile(r'apply|application|register', re.I))
            if app_links:
                application_link = app_links[0]['href']
        
        # Extract required documents
        doc_patterns = [
            r'documents?\s+required[:\s]*([^.\n]+)',
            r'required\s+documents?[:\s]*([^.\n]+)',
            r'(?:aadhaar|land\s+record|bank\s+details|income\s+certificate)'
        ]
        
        documents = []
        for pattern in doc_patterns:
            matches = re.findall(pattern, text, re.I)
            documents.extend([match.strip() for match in matches if match.strip()])
        
        return {
            'scheme_name': scheme_name,
            'eligibility': list(set(eligibility))[:5],  # Limit to 5 most relevant
            'subsidy_amount': subsidy_amount,
            'application_link': application_link,
            'documents_required': list(set(documents))[:5]  # Limit to 5 most relevant
        }
    
    async def _crawl_linked_pages(self, soup: BeautifulSoup, base_url: str, category: str, state_name: Optional[str]) -> List[IndexedContent]:
        """Crawl linked pages for more detailed scheme information"""
        scheme_links = soup.find_all('a', href=True, text=re.compile(r'scheme|subsidy|policy|benefit', re.I))
        
        tasks = []
        for link in scheme_links[:5]:  # Limit to 5 linked pages per page
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only crawl same domain links
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                task = self._index_single_page(full_url, category, urlparse(base_url).netloc, state_name)
                tasks.append(task)
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        content = []
        
        for result in results:
            if isinstance(result, list):
                content.extend(result)
        
        return content
