import re
import json
from collections import defaultdict

def extract_features(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    features = {
        'file': filename,
        'size': len(content),
        'lines': content.count('\n'),
        'backends': [],
        'components': [],
        'scripts': [],
        'styles': []
    }
    
    # Extract backend connections
    backends = re.findall(r'0.0.0.0:\d+', content)
    features['backends'] = list(set(backends))
    
    # Extract script sources
    scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>', content)
    features['scripts'] = scripts
    
    # Extract style/CSS
    styles = re.findall(r'<style[^>]*>([^<]*)</style>', content, re.DOTALL)
    features['styles'] = [s[:100] + '...' for s in styles]
    
    # Extract unique components by keywords
    components = []
    keywords = [
        ('withdrawal', r'withdrawal|withdraw|withdrawing', 'í²°'),
        ('profit', r'profit.*earning|earning.*profit|profit.*mode', 'í³ˆ'),
        ('chart', r'<canvas|Chart\.js|chart.*js', 'í³Š'),
        ('auto-mode', r'auto.*mode|threshold|auto.*withdraw', 'í´–'),
        ('manual-mode', r'manual.*mode|manual.*withdraw', 'í±¤'),
        ('dashboard', r'dashboard|control.*panel', 'í¾›ï¸'),
        ('security', r'security|limit|fee|gas', 'í´’')
    ]
    
    for name, pattern, icon in keywords:
        if re.search(pattern, content, re.IGNORECASE):
            components.append(f"{icon} {name}")
    
    features['components'] = components
    
    return features

# Analyze all HTML files
files = ['dashboard-with-withdrawal.html', 'ultimate-dashboard.html', 'working-dashboard.html']
all_features = {}

for file in files:
    try:
        all_features[file] = extract_features(file)
        print(f"\ní³„ {file}:")
        print(f"   Size: {all_features[file]['size']:,} bytes")
        print(f"   Components: {', '.join(all_features[file]['components'])}")
        print(f"   Backends: {', '.join(all_features[file]['backends'])}")
    except Exception as e:
        print(f"Error analyzing {file}: {e}")

# Save analysis for merging
with open('dashboard_analysis.json', 'w') as f:
    json.dump(all_features, f, indent=2)

print(f"\nâœ… Analysis saved to dashboard_analysis.json")
