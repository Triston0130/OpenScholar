#!/usr/bin/env python3
"""Check if NLM Bookshelf provides PDF URLs"""

import httpx
import asyncio
from xml.etree import ElementTree as ET

async def check_nlm_pdf():
    # First, search for a book
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "books",
        "term": "HIV",
        "retmax": "1",
        "retmode": "xml"
    }
    
    async with httpx.AsyncClient() as client:
        # Search
        search_resp = await client.get(search_url, params=search_params)
        search_root = ET.fromstring(search_resp.text)
        
        id_list = search_root.find("IdList")
        if id_list is not None and len(id_list) > 0:
            book_id = id_list[0].text
            print(f"Found book ID: {book_id}")
            
            # Get book details
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "books",
                "id": book_id,
                "retmode": "xml"
            }
            
            fetch_resp = await client.get(fetch_url, params=fetch_params)
            print(f"\nBook URL: https://www.ncbi.nlm.nih.gov/books/{book_id}/")
            
            # Check if PDF version exists
            # NLM often provides PDFs at /books/NBK{id}/pdf/
            pdf_url = f"https://www.ncbi.nlm.nih.gov/books/{book_id}/pdf/"
            print(f"Potential PDF URL: {pdf_url}")
            
            # Another common pattern
            pdf_url2 = f"https://www.ncbi.nlm.nih.gov/books/NBK{book_id}/pdf/Bookshelf_NBK{book_id}.pdf"
            print(f"Alternative PDF URL: {pdf_url2}")
            
            # Check if the PDF URL exists
            try:
                pdf_check = await client.head(pdf_url, follow_redirects=True)
                print(f"\nPDF URL check ({pdf_url}): {pdf_check.status_code}")
                if pdf_check.status_code == 200:
                    print("✅ PDF is available at this URL!")
            except:
                print("❌ Could not check PDF URL")

if __name__ == "__main__":
    asyncio.run(check_nlm_pdf())