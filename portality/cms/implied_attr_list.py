import markdown
import re
from markdown.extensions import attr_list


def makeExtension(**kwargs):  # pragma: no cover
    return ImpliedAttrListExtension(**kwargs)


class ImpliedAttrListExtension(markdown.Extension):
    """Extension for attatching `attr_list` entries to implied elements.  Specifically: lists and tables"""

    def extendMarkdown(self, md: markdown.Markdown, *args, **kwargs):
        md.preprocessors.register(ImpliedAttrListPreprocessor(md), "implied_attr_list", 100)
        md.treeprocessors.register(ImpliedAttrListTreeprocessor(md), 'implied_attr_list', 100)
        md.registerExtension(self)


class ImpliedAttrListPreprocessor(markdown.preprocessors.Preprocessor):

    def run(self, lines):
        """
        Insert a blank line in between the declaration of the attr_list and the thing that it applies to
        This will allow it to render the list normally.  The attr_list will get rendered into the text of a paragraph
        tag which the Treeprocessor below will handle
        """

        new_lines = []
        for line in lines:
            new_lines.append(line)
            if re.fullmatch(ImpliedAttrListTreeprocessor.BASE_RE, line):
                new_lines.append("")
        return new_lines


class ImpliedAttrListTreeprocessor(attr_list.AttrListTreeprocessor):

    def run(self, doc):
        """
        Iterate through the doc, locating <p> tags that contain ONLY the syntax for attr_lists.

        Once one is found, the value is applied to the next element in the iteration of the doc, and the
        <p> tag is removed

        :param doc:
        :return:
        """
        holdover = None
        removes = []
        for elem in doc.iter():
            if holdover is not None:
                self.assign_attrs(elem, holdover)
                holdover = None

            if elem.tag in ["p"] and elem.text is not None:
                m = re.fullmatch(self.BASE_RE, elem.text)
                if m:
                    holdover = m.group(1)
                    removes.append(elem)

        if len(removes) > 0:
            parent_map = {c: p for p in doc.iter() for c in p}
            for r in removes:
                parent = parent_map[r]
                parent.remove(r)