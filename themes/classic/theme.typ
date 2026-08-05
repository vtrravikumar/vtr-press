#import "page.typ": setup-page, main-matter
#import "typography.typ": setup-typography
#import "headings.typ": setup-headings
#import "metadata.typ": setup-metadata
#import "layout.typ": (
  render-cover,
  render-title-page,
  render-contents,
  render-publisher-imprint,
  part-page,
  front-matter-page,
  chapter-page,
  running-section-page,
  render-scene-title,
  centered-front-matter,
  back-cover-page,
)


#let initialize-theme(
  body,
  book-title: "",
  book-author: "",
) = [
  #setup-page()
  #setup-typography()
  #setup-headings()
  #setup-metadata(
    book-title: book-title,
    book-author: book-author,
  )

  #body
]
