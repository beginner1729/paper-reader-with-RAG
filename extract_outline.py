import re
import sys

tex_file = sys.argv[1]
with open(tex_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all sections and subsections
section_pattern = r'\\(section|subsection)\{([^}]+)\}'
matches = re.findall(section_pattern, content)

outline = []
for match in matches:
    level = match[0]
    title = match[1]
    # Remove label if present
    if '\\label' in title:
        title = title.split('\\label')[0].strip()
    outline.append((level, title))

# Print markdown outline
for level, title in outline:
    if level == 'section':
        print(f'## {title}')
    elif level == 'subsection':
        print(f'### {title}')
    else:
        print(f'#### {title}')

# Also capture abstract and authors? We'll need to parse differently.