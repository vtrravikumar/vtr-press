"""EPUB Renderer v0.1 (Skeleton)"""
from __future__ import annotations
from publication.model import Book,Part,Chapter,Section,Paragraph,Verse,Text,Bold,Italic,Code,Link,Block,Inline

def render(book: Book)->dict[str,str]:
    return _Renderer().render(book)

class _Renderer:
    def __init__(self):
        self.documents={}
    def render(self,book:Book)->dict[str,str]:
        self._render_book(book)
        return self.documents
    def _render_book(self,book:Book)->None:
        self.documents["index.xhtml"]=self._document(book.metadata.title,self._render_title_page(book))
    def _render_title_page(self,book:Book)->str:
        return f"<h1>{book.metadata.title}</h1>\n<p>{book.metadata.author}</p>"
    def _document(self,title:str,body:str)->str:
        return f'<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"/><title>{title}</title></head><body>{body}</body></html>'
    def _render_section(self,section:Section)->None: raise NotImplementedError
    def _render_part(self,part:Part)->None: raise NotImplementedError
    def _render_chapter(self,chapter:Chapter)->None: raise NotImplementedError
    def _render_block(self,block:Block)->str:
        if isinstance(block,Paragraph): return self._render_paragraph(block)
        if isinstance(block,Verse): return self._render_verse(block)
        raise TypeError(type(block).__name__)
    def _render_paragraph(self,p:Paragraph)->str:
        return "<p>"+"".join(self._render_inline(n) for n in p.children)+"</p>"
    def _render_verse(self,v:Verse)->str:
        return '<div class="verse">'+"<br/>".join(v.lines)+"</div>"
    def _render_inline(self,node:Inline)->str:
        if isinstance(node,Text): return node.text
        if isinstance(node,Bold): return "<strong>"+"".join(self._render_inline(c) for c in node.children)+"</strong>"
        if isinstance(node,Italic): return "<em>"+"".join(self._render_inline(c) for c in node.children)+"</em>"
        if isinstance(node,Code): return f"<code>{node.text}</code>"
        if isinstance(node,Link): return f'<a href="{node.url}">{node.text}</a>'
        raise TypeError(type(node).__name__)
