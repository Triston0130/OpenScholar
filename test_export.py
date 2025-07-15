#!/usr/bin/env python3
"""
Test script for OpenScholar export functionality
"""
import asyncio
import json
from app.models import SearchRequest, ExportRequest, Paper
from app.services import SearchService
from app.export import ExportService

async def test_export_functionality():
    """Test all export formats with real data"""
    print("🧪 Testing OpenScholar Export Functionality")
    print("=" * 50)
    
    search_service = SearchService()
    export_service = ExportService()
    
    try:
        # First, get some real papers to export
        print("🔍 Fetching sample papers...")
        search_request = SearchRequest(
            query="child nutrition",
            year_start=2020,
            year_end=2024
        )
        
        papers, sources = await search_service.search(search_request)
        print(f"✅ Found {len(papers)} papers to test export")
        
        if not papers:
            print("❌ No papers found for testing")
            return
        
        # Limit to first 5 papers for testing
        test_papers = papers[:5]
        print(f"📊 Testing export with {len(test_papers)} papers")
        print()
        
        # Test each export format
        formats = ["csv", "json", "bib"]
        
        for format_type in formats:
            print(f"📄 Testing {format_type.upper()} export...")
            
            try:
                # Create export request
                export_request = ExportRequest(
                    papers=test_papers,
                    format=format_type
                )
                
                # Perform export
                content, filename, mime_type = export_service.export_papers(export_request)
                
                print(f"  ✅ Success!")
                print(f"  📁 Filename: {filename}")
                print(f"  🔧 MIME type: {mime_type}")
                print(f"  📏 Content length: {len(content)} characters")
                
                # Show sample content
                if format_type == "csv":
                    lines = content.split('\\n')[:3]  # First 3 lines
                    print(f"  📝 Sample CSV content:")
                    for line in lines:
                        print(f"    {line[:80]}..." if len(line) > 80 else f"    {line}")
                
                elif format_type == "json":
                    try:
                        data = json.loads(content)
                        print(f"  📝 JSON structure:")
                        print(f"    - Export metadata: ✅")
                        print(f"    - Papers count: {len(data.get('papers', []))}")
                        if data.get('papers'):
                            sample_paper = data['papers'][0]
                            print(f"    - Sample title: {sample_paper.get('title', '')[:50]}...")
                    except json.JSONDecodeError:
                        print(f"  ❌ Invalid JSON generated")
                
                elif format_type == "bib":
                    entries = content.count('@article')
                    print(f"  📝 BibTeX entries: {entries}")
                    # Show first entry preview
                    first_entry = content.split('@article')[1].split('}')[0] if '@article' in content else ""
                    if first_entry:
                        lines = first_entry.split('\\n')[:3]
                        print(f"  📖 Sample entry preview:")
                        for line in lines:
                            print(f"    @article{line}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Export failed: {e}")
                print()
        
        print("🎉 Export testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await search_service.close()

async def test_sample_bibtex():
    """Test BibTeX generation with sample data"""
    print("\\n📚 Testing BibTeX with sample data...")
    
    # Create sample papers
    sample_papers = [
        Paper(
            title="The role of nutrition in early development",
            authors=["Smith, John", "Doe, Jane"],
            abstract="This study examines the critical role of nutrition in early childhood development...",
            year="2021",
            source="Europe PMC",
            doi="10.1234/abc123",
            full_text_url="https://example.com/paper1.pdf",
            journal="Journal of Early Childhood Research"
        ),
        Paper(
            title="Educational interventions for healthy eating habits",
            authors=["Johnson, Mary", "Brown, David"],
            abstract="An analysis of educational programs designed to promote healthy eating...",
            year="2022",
            source="ERIC",
            doi="10.5678/def456",
            full_text_url="https://example.com/paper2.pdf",
            journal="Educational Psychology Review"
        )
    ]
    
    export_service = ExportService()
    
    try:
        export_request = ExportRequest(
            papers=sample_papers,
            format="bib"
        )
        
        content, filename, mime_type = export_service.export_papers(export_request)
        
        print(f"✅ BibTeX export successful!")
        print(f"📁 Filename: {filename}")
        print(f"📄 Generated BibTeX:")
        print("-" * 40)
        print(content)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ BibTeX test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_export_functionality())
    asyncio.run(test_sample_bibtex())