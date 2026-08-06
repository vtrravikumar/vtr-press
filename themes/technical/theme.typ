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
) = {
  // NOTE: this theme's initialize-theme differs internally from
  // themes/classic's (which calls each setup-* function with no
  // arguments inside a content block, then `#body` separately).
  // That pattern silently fails to apply setup-headings()'s `show`
  // rules -- Typst's `show`/`set` rules are scoped to the block in
  // which they're declared and do not propagate out of a function
  // call to sibling content in the caller. Since this theme requires
  // working heading numbering (see headings.typ), setup-headings
  // here takes `body` and returns it as its final statement so the
  // rules and the content they style share one lexical scope.
  //
  // setup-page / setup-typography / setup-metadata are unaffected --
  // they use plain, unscoped `set` statements, which do propagate
  // correctly across a function call -- so they keep the same
  // no-argument call convention as themes/classic for consistency.
  //
  // The public signature of initialize-theme itself (body, book-title,
  // book-author) is unchanged and matches themes/classic exactly.
  setup-page()
  setup-typography()
  setup-metadata(
    book-title: book-title,
    book-author: book-author,
  )

  setup-headings(body)
}
