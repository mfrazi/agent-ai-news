"""MkDocs hooks that sanitize pages before they are published.

Reports are written by an LLM from untrusted web content, and titles come from user queries.
MkDocs passes raw HTML in markdown straight through, and themes render page titles unescaped,
so both are cleaned here before anything reaches the static site. Registered in mkdocs.yml.
"""

import html

import nh3

# Everything the markdown extensions in mkdocs.yml emit; anything else (script, iframe, form, ...) is removed.
ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "caption", "code", "col", "colgroup", "dd", "del",
    "details", "div", "dl", "dt", "em", "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6",
    "hr", "i", "img", "input", "ins", "kbd", "label", "li", "mark", "ol", "p", "pre", "s", "samp",
    "small", "span", "strong", "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "u", "ul", "var",
}
ALLOWED_ATTRIBUTES = {
    "*": {"class", "id", "title"},
    "a": {"href", "name"},
    "img": {"src", "alt", "width", "height"},
    "input": {"checked", "disabled"},  # pymdownx.tasklist checkboxes; `type` is limited by value below
    "label": {"for"},
    "ol": {"start"},
    "td": {"colspan", "rowspan", "style"},
    "th": {"colspan", "rowspan", "style"},
}


def sanitize_html(content: str) -> str:
    """Reduce rendered page HTML to the allowlist; drops event handlers and javascript:/data: URLs."""
    return nh3.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        tag_attribute_values={"input": {"type": {"checkbox"}}},
        url_schemes={"http", "https", "mailto"},
        filter_style_properties={"text-align"},  # table column alignment
    )


def on_page_markdown(markdown, page, **kwargs):
    """Escape the frontmatter title, which themes insert into the nav and header as raw HTML."""
    title = page.meta.get("title")
    if isinstance(title, str):
        page.meta["title"] = html.escape(title, quote=False)
    return markdown


def on_page_content(content, **kwargs):
    """Sanitize the rendered body of every page (reports and the archive index)."""
    return sanitize_html(content)
