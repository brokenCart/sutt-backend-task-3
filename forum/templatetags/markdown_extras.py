import bleach
import markdown
from django import template

register = template.Library()


@register.filter
def markdownify(text):
    html = markdown.markdown(
        text, extensions=["fenced_code", "tables", "nl2br", "sane_lists", "extra"]
    )
    clean_html = bleach.clean(
        html,
        tags=list(bleach.sanitizer.ALLOWED_TAGS)
        + [
            "p",
            "pre",
            "code",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "ul",
            "ol",
            "li",
            "blockquote",
            "br",
            "img",
            "a",
        ],
        attributes={
            **bleach.sanitizer.ALLOWED_ATTRIBUTES,
            "img": ["src", "alt", "title"],
            "a": ["href", "title", "rel"],
        },
    )
    return clean_html
