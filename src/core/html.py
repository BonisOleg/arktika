"""HTML CMS-полів: bleach (SEC-04) + Enter-контракт admin_cms_blocks_skill."""
from __future__ import annotations

import html
import re

import bleach
from django.utils.html import strip_tags

ALLOWED_TAGS = ["b", "i", "em", "strong", "u", "p", "br", "ul", "ol", "li", "a"]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]

_EMPTY_P_RE = re.compile(r"<p\b[^>]*>\s*(?:&nbsp;|\xa0|<br\s*/?>|\s)*</p>", re.I)
_ADJACENT_P_RE = re.compile(r"</p>\s*<p\b[^>]*>", re.I)
_PARA_MARK = "[[[PTPARA]]]"


def sanitize_cms_html(value: str | None) -> str:
    raw = value or ""
    return bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def html_to_plain(value: str | None) -> str:
    text = _EMPTY_P_RE.sub(_PARA_MARK, str(value or ""))
    text = _ADJACENT_P_RE.sub("\n", text)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</h[1-6]>|</li>|</tr>", "\n", text, flags=re.I)
    text = html.unescape(strip_tags(text)).replace("\xa0", " ").replace(_PARA_MARK, "\n\n")
    return re.sub(r"\n{3,}", "\n\n", text.replace("\r\n", "\n")).strip()
