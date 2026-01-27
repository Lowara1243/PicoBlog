import os
import re
from flask import Flask

# Mock config for standalone test
class Config:
    MARKDOWN_ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul', 'del', 'ins', 'sup', 'sub']
    MARKDOWN_ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
        'div': ['class', 'style'],
        'span': ['class', 'style', 'data-lang'],
        'code': ['class', 'style'],
        'pre': ['class', 'style'],
    }
    MARKDOWN_ALLOWED_PROTOCOLS = ['http', 'https']

app = Flask(__name__)
app.config.from_object(Config)

import markdown2
import bleach

def render_markdown(text):
    def inject_lang_marker(match):
        lang = match.group(1)
        if lang:
            return f'<span class="code-lang-marker" data-lang="{lang}"></span>\n\n' + match.group(0)
        return match.group(0)

    text_with_markers = re.sub(r'^```(\w+)', inject_lang_marker, text, flags=re.MULTILINE)
    
    html = markdown2.markdown(text_with_markers, extras=['fenced-code-blocks'])
    
    clean_html = bleach.clean(
        html,
        tags=app.config['MARKDOWN_ALLOWED_TAGS'],
        attributes=app.config['MARKDOWN_ALLOWED_ATTRIBUTES'],
        protocols=app.config['MARKDOWN_ALLOWED_PROTOCOLS'],
        strip=True
    )
    return clean_html

with app.app_context():
    print("--- RAW RENDER ---")
    print(render_markdown('```python\nprint(1)\n```'))
