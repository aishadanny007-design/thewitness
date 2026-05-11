#!/usr/bin/env python3
"""
Generate XML sitemap for The Witness diary entries.
Run this script to create/update sitemap.xml with all diary entries.
"""

import os
import json
from datetime import datetime
from pathlib import Path

def generate_sitemap(diary_path='diary', output_path='sitemap.xml', base_url='https://thewitness.ai'):
    """
    Generate sitemap.xml from diary entries.
    
    Args:
        diary_path: Path to diary directory
        output_path: Where to write sitemap.xml
        base_url: Base URL for the site
    """
    
    entries = []
    
    # Find all diary entries
    for year_dir in Path(diary_path).glob('*/'):
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.glob('*/'):
            if not month_dir.is_dir():
                continue
            for entry_file in month_dir.glob('*.md'):
                date_str = entry_file.stem  # e.g., "2026-05-04"
                # Get file modification time
                mod_time = datetime.fromtimestamp(entry_file.stat().st_mtime)
                entries.append({
                    'date': date_str,
                    'path': str(entry_file),
                    'lastmod': mod_time.isoformat()
                })
    
    # Sort entries by date
    entries.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
        '',
        '  <!-- Homepage -->',
        f'  <url>',
        f'    <loc>{base_url}/</loc>',
        f'    <lastmod>{datetime.now().isoformat()}</lastmod>',
        f'    <changefreq>daily</changefreq>',
        f'    <priority>1.0</priority>',
        f'  </url>',
        '',
    ]
    
    # Add entries
    for i, entry in enumerate(entries):
        priority = str(1.0 - (i * 0.01))[:4]  # Decreasing priority for older entries
        xml_lines.extend([
            f'  <!-- Diary Entry: {entry["date"]} -->',
            f'  <url>',
            f'    <loc>{base_url}/#entry</loc>',
            f'    <lastmod>{entry["lastmod"]}</lastmod>',
            f'    <changefreq>never</changefreq>',
            f'    <priority>{priority}</priority>',
            f'    <news:news>',
            f'      <news:publication>',
            f'        <news:name>The Witness</news:name>',
            f'        <news:language>en</news:language>',
            f'      </news:publication>',
            f'      <news:publication_date>{entry["lastmod"]}</news:publication_date>',
            f'      <news:title>The Witness Entry - {entry["date"]}</news:title>',
            f'    </news:news>',
            f'  </url>',
            '',
        ])
    
    xml_lines.extend([
        '  <!-- About -->',
        f'  <url>',
        f'    <loc>{base_url}/#about</loc>',
        f'    <changefreq>monthly</changefreq>',
        f'    <priority>0.8</priority>',
        f'  </url>',
        '',
        '  <!-- Archive -->',
        f'  <url>',
        f'    <loc>{base_url}/#archive</loc>',
        f'    <changefreq>daily</changefreq>',
        f'    <priority>0.9</priority>',
        f'  </url>',
        '',
        '</urlset>',
    ])
    
    # Write sitemap
    with open(output_path, 'w') as f:
        f.write('\n'.join(xml_lines))
    
    print(f"✓ Sitemap generated: {output_path}")
    print(f"✓ Entries included: {len(entries)}")
    
    return len(entries)


def generate_rss_feed(diary_path='diary', output_path='feed.xml', base_url='https://thewitness.ai'):
    """
    Generate RSS feed for diary entries.
    
    Args:
        diary_path: Path to diary directory
        output_path: Where to write RSS feed
        base_url: Base URL for the site
    """
    
    entries = []
    
    # Find all diary entries (limit to 20 most recent)
    entry_dict = {}
    for year_dir in Path(diary_path).glob('*/'):
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.glob('*/'):
            if not month_dir.is_dir():
                continue
            for entry_file in month_dir.glob('*.md'):
                date_str = entry_file.stem
                mod_time = datetime.fromtimestamp(entry_file.stat().st_mtime)
                
                # Read first line as title
                try:
                    with open(entry_file, 'r') as f:
                        first_line = f.readline().strip().replace('# ', '')
                        # Read next few lines for description
                        description = f.read(500)
                except:
                    first_line = f"Entry for {date_str}"
                    description = "Read the full entry on The Witness"
                
                entry_dict[date_str] = {
                    'date': date_str,
                    'title': first_line or f"Entry for {date_str}",
                    'description': description,
                    'pubDate': mod_time,
                    'lastmod': mod_time.isoformat()
                }
    
    # Sort and get 20 most recent
    entries = sorted(entry_dict.values(), key=lambda x: x['date'], reverse=True)[:20]
    
    # Generate RSS
    rss_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        f'    <title>The Witness - AI Diary</title>',
        f'    <link>{base_url}</link>',
        f'    <description>An AI-powered daily diary documenting world events, internet culture, and technology</description>',
        f'    <language>en-us</language>',
        f'    <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml" />',
        f'    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>',
        '',
    ]
    
    for entry in entries:
        rss_lines.extend([
            f'    <item>',
            f'      <title>{entry["title"]}</title>',
            f'      <link>{base_url}/#entry?date={entry["date"]}</link>',
            f'      <guid>{base_url}/#entry?date={entry["date"]}</guid>',
            f'      <pubDate>{entry["pubDate"].strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate>',
            f'      <description><![CDATA[{entry["description"]}...]]></description>',
            f'    </item>',
            '',
        ])
    
    rss_lines.extend([
        '  </channel>',
        '</rss>',
    ])
    
    # Write RSS feed
    with open(output_path, 'w') as f:
        f.write('\n'.join(rss_lines))
    
    print(f"✓ RSS Feed generated: {output_path}")
    print(f"✓ Recent entries included: {len(entries)}")
    
    return len(entries)


if __name__ == '__main__':
    import sys
    
    print("Generating sitemap and RSS feed for The Witness...")
    print()
    
    # Get current working directory
    cwd = os.getcwd()
    
    # Generate sitemap
    try:
        sitemap_count = generate_sitemap(
            diary_path=os.path.join(cwd, 'diary'),
            output_path=os.path.join(cwd, 'sitemap.xml')
        )
    except Exception as e:
        print(f"✗ Error generating sitemap: {e}")
        sitemap_count = 0
    
    print()
    
    # Generate RSS feed
    try:
        rss_count = generate_rss_feed(
            diary_path=os.path.join(cwd, 'diary'),
            output_path=os.path.join(cwd, 'feed.xml')
        )
    except Exception as e:
        print(f"✗ Error generating RSS feed: {e}")
        rss_count = 0
    
    print()
    print(f"Summary: {sitemap_count} entries in sitemap, {rss_count} entries in RSS feed")
