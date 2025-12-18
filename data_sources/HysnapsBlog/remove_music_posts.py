import xml.etree.ElementTree as ET
from pathlib import Path

# Parse the XML file
xml_file = Path(__file__).parent / "data_sources/HysnapsBlog/hysnapsmusicandmentalhealth.wordpress.com-2025-12-17-10_23_08/hysnapsmusicandmentalhealth.wordpress.com.2025-12-17.000.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

# Find all items (posts)
channel = root.find('channel')
items = channel.findall('item')
print(f'Total items before: {len(items)}')

# Find and remove items with music category/tag
items_to_remove = []
for item in items:
    categories = item.findall('category')
    for cat in categories:
        nicename = cat.get('nicename', '')
        if nicename.lower() == 'music':
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else 'No title'
            print(f'Removing: {title}')
            items_to_remove.append(item)
            break

# Remove the items
for item in items_to_remove:
    channel.remove(item)

print(f'Total items after: {len(channel.findall("item"))}')

# Write back to file
ET.register_namespace('excerpt', 'http://wordpress.org/export/1.2/excerpt/')
ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
ET.register_namespace('wfw', 'http://wellformedweb.org/CommentAPI/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
ET.register_namespace('wp', 'http://wordpress.org/export/1.2/')

tree.write(xml_file, encoding='UTF-8', xml_declaration=True)
print(f'\nFile saved: {xml_file}')
print(f'✓ Successfully removed {len(items_to_remove)} posts with music tag')
