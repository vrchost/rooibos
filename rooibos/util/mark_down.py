import bleach as bleach
import markdown as py_markdown
from bleach_whitelist import markdown_tags, markdown_attrs


# allow link targets
markdown_attrs['a'].append('target')


def markdown(text):
    return bleach.clean(
        py_markdown.markdown(text, extensions=['attr_list']),
        markdown_tags,
        markdown_attrs
    )
