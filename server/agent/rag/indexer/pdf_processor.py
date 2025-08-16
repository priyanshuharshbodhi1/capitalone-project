"""
PDF Processor for Government Agricultural Documents

Processes official PDFs, notifications, and scheme documents from government sources.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
import PyPDF2
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class PDFContent:
    url: str
    title: str
    content: str
    scheme_name: Optional[str]
    eligibility: List[str]
    subsidy_details: Optional[str]
    application_process: Optional[str]
    documents_required: List[str]
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    issuing_authority: Optional[str]
    metadata: Dict[str, Any]

class PDFProcessor:
    """Process government agricultural PDFs and extract scheme information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common government PDF sources
        self.pdf_sources = {
            'central_notifications': [
                'https://pmkisan.gov.in/Documents/',
                'https://agricoop.nic.in/documents/',
                'https://dahd.nic.in/documents/',
                'https://pmfby.gov.in/pdf/',
                'https://pmksy.gov.in/Documents/'
            ],
            'scheme_guidelines': [
                'https://pmkisan.gov.in/Notifications/',
                'https://krishi.gov.in/Documents/',
                'https://fpo.gov.in/documents/'
            ]
        }
    
    async def process_all_pdfs(self) -> List[PDFContent]:
        """Process all government PDF sources"""
        self.logger.info("Starting PDF processing for government documents...")
        
        all_pdf_content = []
        
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'GovtPDFProcessor/1.0'}
        ) as session:
            
            for category, urls in self.pdf_sources.items():
                self.logger.info(f"Processing {category} PDFs...")
                
                tasks = []
                for base_url in urls:
                    task = self._discover_and_process_pdfs(session, base_url, category)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        all_pdf_content.extend(result)
                    elif isinstance(result, Exception):
                        self.logger.error(f"Error processing PDF category {category}: {result}")
        
        self.logger.info(f"PDF processing completed. Total PDFs processed: {len(all_pdf_content)}")
        return all_pdf_content
    
    async def _discover_and_process_pdfs(self, session: aiohttp.ClientSession, base_url: str, category: str) -> List[PDFContent]:
        """Discover and process PDFs from a base URL"""
        try:
            # First, get the directory listing or webpage
            async with session.get(base_url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to access {base_url}: {response.status}")
                    return []
                
                html_content = await response.text()
                
            # Extract PDF links from the page
            pdf_urls = self._extract_pdf_links(html_content, base_url)
            
            # Process each PDF
            tasks = []
            for pdf_url in pdf_urls[:10]:  # Limit to 10 PDFs per source
                task = self._process_single_pdf(session, pdf_url, category)
                tasks.append(task)
            
            if not tasks:
                return []
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            pdf_contents = []
            for result in results:
                if isinstance(result, PDFContent):
                    pdf_contents.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Error processing PDF: {result}")
            
            return pdf_contents
            
        except Exception as e:
            self.logger.error(f"Error discovering PDFs from {base_url}: {e}")
            return []
    
    def _extract_pdf_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract PDF links from HTML content"""
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(html_content, 'html.parser')
        pdf_links = []
        
        # Find all links ending with .pdf
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
        
        return pdf_links
    
    async def _process_single_pdf(self, session: aiohttp.ClientSession, pdf_url: str, category: str) -> PDFContent:
        """Process a single PDF document"""
        try:
            self.logger.info(f"Processing PDF: {pdf_url}")
            
            # Download PDF
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download PDF: {response.status}")
                
                pdf_data = await response.read()
            
            # Extract text from PDF
            text_content = self._extract_text_from_pdf(pdf_data)
            
            if not text_content or len(text_content) < 100:
                raise Exception("PDF content too short or empty")
            
            # Parse scheme information from PDF content
            scheme_info = self._parse_pdf_scheme_info(text_content)
            
            return PDFContent(
                url=pdf_url,
                title=scheme_info['title'],
                content=text_content,
                scheme_name=scheme_info['scheme_name'],
                eligibility=scheme_info['eligibility'],
                subsidy_details=scheme_info['subsidy_details'],
                application_process=scheme_info['application_process'],
                documents_required=scheme_info['documents_required'],
                effective_date=scheme_info['effective_date'],
                expiry_date=scheme_info['expiry_date'],
                issuing_authority=scheme_info['issuing_authority'],
                metadata={
                    'category': category,
                    'file_size': len(pdf_data),
                    'processed_at': datetime.now()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_url}: {e}")
            raise
    
    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text content from PDF using PyPDF2"""
        text_content = ""
        
        try:
            # Use PyPDF2 for text extraction
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed: {e}")
        
        return text_content
    
    def _parse_pdf_scheme_info(self, text: str) -> Dict[str, Any]:
        """Parse scheme information from PDF text content"""
        
        # Extract title (usually in first few lines)
        lines = text.split('\n')[:10]
        title = None
        for line in lines:
            if len(line.strip()) > 10 and not line.strip().isupper():
                title = line.strip()
                break
        
        # Extract scheme name
        scheme_patterns = [
            r'(?:scheme|yojana|programme|program)[:\s]*([^\n.]+)',
            r'([A-Z][^\n.]*(?:scheme|yojana|programme|program)[^\n.]*)',
            r'(?:notification|circular|order)[:\s]*([^\n.]+)'
        ]
        
        scheme_name = None
        for pattern in scheme_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                scheme_name = match.group(1).strip()
                break
        
        # Extract eligibility criteria
        eligibility_section = self._extract_section(text, r'eligibility|eligible|criteria')
        eligibility = self._parse_list_items(eligibility_section) if eligibility_section else []
        
        # Extract subsidy details
        subsidy_section = self._extract_section(text, r'subsidy|financial\s+assistance|grant|benefit')
        subsidy_details = subsidy_section[:500] if subsidy_section else None
        
        # Extract application process
        application_section = self._extract_section(text, r'application|apply|procedure|process')
        application_process = application_section[:500] if application_section else None
        
        # Extract required documents
        docs_section = self._extract_section(text, r'documents?|papers?|certificates?')
        documents_required = self._parse_list_items(docs_section) if docs_section else []
        
        # Extract dates
        effective_date = self._extract_date(text, r'effective\s+from|w\.e\.f|from\s+date')
        expiry_date = self._extract_date(text, r'valid\s+till|up\s+to|expiry|last\s+date')
        
        # Extract issuing authority
        authority_patterns = [
            r'(?:ministry|department|government)[:\s]*([^\n.]+)',
            r'issued\s+by[:\s]*([^\n.]+)',
            r'([^\n.]*ministry[^\n.]*)',
            r'([^\n.]*department[^\n.]*)'
        ]
        
        issuing_authority = None
        for pattern in authority_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                issuing_authority = match.group(1).strip()
                break
        
        return {
            'title': title or 'Government Document',
            'scheme_name': scheme_name,
            'eligibility': eligibility[:5],
            'subsidy_details': subsidy_details,
            'application_process': application_process,
            'documents_required': documents_required[:5],
            'effective_date': effective_date,
            'expiry_date': expiry_date,
            'issuing_authority': issuing_authority
        }
    
    def _extract_section(self, text: str, section_pattern: str) -> Optional[str]:
        """Extract a specific section from PDF text"""
        pattern = rf'({section_pattern})[:\s]*([^§]*?)(?:\n\s*\n|\Z)'
        match = re.search(pattern, text, re.I | re.DOTALL)
        
        if match:
            return match.group(2).strip()
        return None
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items from text section"""
        if not text:
            return []
        
        # Look for bullet points, numbered lists, etc.
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with bullet or number
            if re.match(r'^[•\-*]\s+|^\d+[\.)]\s+|^[a-z][\.)]\s+', line):
                item = re.sub(r'^[•\-*\d+a-z\.)]\s+', '', line).strip()
                if len(item) > 5:
                    items.append(item)
        
        return items[:5]  # Limit to 5 items
    
    def _extract_date(self, text: str, date_pattern: str) -> Optional[datetime]:
        """Extract dates from text"""
        pattern = rf'{date_pattern}[:\s]*([^\n.]+)'
        match = re.search(pattern, text, re.I)
        
        if not match:
            return None
        
        date_str = match.group(1).strip()
        
        # Try to parse various date formats
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})',  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str, re.I)
            if match:
                try:
                    if 'jan|feb|mar' in pattern:  # Month format
                        day, month_str, year = match.groups()
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(month_str.lower()[:3])
                        if month:
                            return datetime(int(year), month, int(day))
                    else:
                        parts = [int(x) for x in match.groups()]
                        if len(parts) == 3:
                            if parts[2] > 31:  # Year is last
                                return datetime(parts[2], parts[1], parts[0])
                            else:  # Year is first
                                return datetime(parts[0], parts[1], parts[2])
                except (ValueError, TypeError):
                    continue
        
        return None
