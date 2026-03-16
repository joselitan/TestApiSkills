#!/usr/bin/env python3
"""
PDF Generator for QA Test Platform Manuals
Converts HTML manuals to professional PDFs
"""

import os
import sys
from pathlib import Path

try:
    import pdfkit
    import markdown
    from jinja2 import Template
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install pdfkit markdown jinja2")
    print("Also install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
    sys.exit(1)


def generate_pdf_from_html(html_file, output_file):
    """Generate PDF from HTML file"""
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
        'print-media-type': None,
    }
    
    try:
        pdfkit.from_file(html_file, output_file, options=options)
        print(f"✅ PDF generated: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False


def generate_pdf_from_markdown(md_file, output_file):
    """Generate PDF from Markdown file"""
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML
    html_content = markdown.markdown(md_content, extensions=['codehilite', 'tables', 'toc'])
    
    # HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>QA Test Platform Manual</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
            h1 { color: #2563eb; border-bottom: 2px solid #2563eb; }
            h2 { color: #2563eb; margin-top: 30px; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 5px; }
            code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #2563eb; color: white; }
        </style>
    </head>
    <body>
        {{ content }}
    </body>
    </html>
    """
    
    template = Template(html_template)
    full_html = template.render(content=html_content)
    
    # Save temporary HTML file
    temp_html = output_file.replace('.pdf', '_temp.html')
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    # Generate PDF
    success = generate_pdf_from_html(temp_html, output_file)
    
    # Clean up
    if os.path.exists(temp_html):
        os.remove(temp_html)
    
    return success


def main():
    """Generate PDFs for all manuals"""
    base_dir = Path(__file__).parent.parent
    
    manuals = [
        {
            'name': 'Quick Start Guide',
            'html': base_dir / 'quick-start' / 'quick-start-guide.html',
            'md': base_dir / 'quick-start' / 'quick-start-guide.md',
            'pdf': base_dir / 'quick-start' / 'quick-start-guide.pdf'
        }
    ]
    
    print("🚀 Generating PDFs for QA Test Platform Manuals...")
    
    for manual in manuals:
        print(f"\n📄 Processing: {manual['name']}")
        
        # Try HTML first, then Markdown
        if manual['html'].exists():
            success = generate_pdf_from_html(str(manual['html']), str(manual['pdf']))
        elif manual['md'].exists():
            success = generate_pdf_from_markdown(str(manual['md']), str(manual['pdf']))
        else:
            print(f"❌ No source file found for {manual['name']}")
            continue
        
        if success:
            print(f"✅ {manual['name']} PDF created successfully")
        else:
            print(f"❌ Failed to create {manual['name']} PDF")
    
    print("\n🎉 PDF generation complete!")


if __name__ == "__main__":
    main()