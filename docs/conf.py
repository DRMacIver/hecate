import sys
import os
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Hecate'
copyright = '2015, David R. MacIver'
author = 'David R. MacIver'
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "src")
)
from hecate import __version__
version = __version__
release = __version__
language = None
exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'Hecatedoc'
latex_elements = {
}
latex_documents = [(
    master_doc, 'Hecate.tex', 'Hecate Documentation',
    'David R. MacIver', 'manual'
)]
man_pages = [
    (master_doc, 'hecate', 'Hecate Documentation',
     [author], 1)
]
texinfo_documents = [(
    master_doc, 'Hecate', 'Hecate Documentation',
    author, 'Hecate', 'One line description of project.',
    'Miscellaneous'
)]
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ['search.html']
