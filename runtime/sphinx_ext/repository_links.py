"""Resolve repository-style directory links to their README or index page."""
import posixpath
from urllib.parse import urlsplit

from sphinx.util.nodes import make_refnode


def resolve_directory(app, env, node, content):
    target = urlsplit(node.get('reftarget', ''))
    if target.scheme or target.netloc or not target.path.endswith('/'):
        return None
    refdoc = node.get('refdoc', env.docname)
    directory = posixpath.normpath(posixpath.join(posixpath.dirname(refdoc), target.path))
    if target.path.startswith('/'):
        directory = directory.lstrip('/')
    for entry in ('README', 'index'):
        document = posixpath.join(directory, entry)
        if document in env.found_docs:
            return make_refnode(app.builder, refdoc, document, target.fragment or None, content)
    return None


def setup(app):
    app.connect('missing-reference', resolve_directory)
    return {'version': '1.0', 'parallel_read_safe': True, 'parallel_write_safe': True}
