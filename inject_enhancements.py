#!/usr/bin/env python3
"""
WASH4U Website Enhancement Injector
Injects the enhancement script into all HTML pages
"""

import os
import re
import glob

BASE_DIR = "/Volumes/Hogwards/AITOXR_PRODUCTS/WASH4U"
ENHANCEMENT_SCRIPT = '<script src="/_next/static/wash4u-enhancements.js" defer></script>'
THEME_COLOR_META = '<meta name="theme-color" content="#21b14b"/>'
MANIFEST_LINK = '<link rel="manifest" href="/manifest.json"/>'

# Additional meta improvements
ADDITIONAL_META = f'''
{THEME_COLOR_META}
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="default"/>
<meta name="apple-mobile-web-app-title" content="Wash4U"/>
<meta name="format-detection" content="telephone=yes"/>
<meta name="mobile-web-app-capable" content="yes"/>
'''

def inject_enhancements(file_path):
    """Inject enhancement script and meta tags into an HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already enhanced
    if 'wash4u-enhancements.js' in content:
        return False
    
    # Inject enhancement script before closing </body>
    if '</body>' in content:
        content = content.replace('</body>', f'{ENHANCEMENT_SCRIPT}\n</body>')
    elif '</html>' in content:
        content = content.replace('</html>', f'{ENHANCEMENT_SCRIPT}\n</html>')
    
    # Inject meta tags after viewport meta
    viewport_pattern = r'(<meta name="viewport" content="[^"]+"/?>)'
    if re.search(viewport_pattern, content) and THEME_COLOR_META not in content:
        content = re.sub(viewport_pattern, r'\1\n' + ADDITIONAL_META.strip(), content, count=1)
    
    # Add manifest link after favicon
    if '<link rel="icon"' in content and MANIFEST_LINK not in content:
        content = re.sub(
            r'(<link rel="icon"[^>]+>)',
            r'\1\n' + MANIFEST_LINK,
            content,
            count=1
        )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    html_files = glob.glob(os.path.join(BASE_DIR, '**/index.html'), recursive=True)
    html_files += glob.glob(os.path.join(BASE_DIR, '404.html'), recursive=True)
    
    enhanced_count = 0
    for file_path in html_files:
        if inject_enhancements(file_path):
            enhanced_count += 1
            print(f"✓ Enhanced: {os.path.relpath(file_path, BASE_DIR)}")
    
    print(f"\n{'='*50}")
    print(f"Total pages enhanced: {enhanced_count}")
    print(f"Total pages checked: {len(html_files)}")

if __name__ == '__main__':
    main()
