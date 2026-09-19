#import "functions.typ": current-chapter-title
#import "page.typ": plain-page, running-page


// Technical documents are published as interior-only documents with
// no embedded cover page. This function is kept (rather than removed)
// solely to preserve the same public API as themes/classic, so the
// renderer can call it without theme-specific branching. It
// intentionally renders nothing.
#let render-cover(cover-path) = {}


#let render-title-page(
  title: "",
  subtitle: "",
  author: "",
  authors: (),
  copyright-year: "",
  show-publisher-logo: true,
  publisher-logo: "/assets/publisher/logo.png",
  publisher-name: "",
  publisher-name-lines: (),
) = {
  plain-page[
    #align(center)[
      // Keep the title-page content as one fitting block. The previous
      // fixed percentage spacings (20% + 12% + 20%) could consume more
      // than half the page before the title, subtitle, authors, logo,
      // and copyright were laid out. With multiple authors this could
      // push the final author onto a new page. Fractional spacings
      // balance only the remaining space and therefore adapt to the
      // number of authors.
      #v(1fr)

      #text(size: 24pt, weight: "bold")[#title]

      #if subtitle != "" {
        v(1.5em)
        text(size: 13pt)[#subtitle]
      }

      #v(3em)

      #if authors.len() > 0 {
        for (index, author) in authors.enumerate() {
          text(size: 13pt)[#author]
          if index < authors.len() - 1 {
            linebreak()
          }
        }
      } else {
        text(size: 13pt)[#author]
      }

      #v(3em)

      #align(center)[
        #if show-publisher-logo {
          image(publisher-logo, width: 20mm)
          v(2mm)
        }
        #if publisher-name-lines.len() > 0 {
          for line in publisher-name-lines {
            text(size: 10pt)[#line]
            linebreak()
          }
          v(1mm)
        } else if publisher-name != "" {
          text(size: 10pt)[#publisher-name]
          v(1mm)
        }
        #text(size: 10pt)[#copyright-year]
      ]

      #v(1fr)
    ]
  ]
}


#let render-contents() = {
  plain-page[
    #align(left)[
      #text(
        size: 18pt,
        weight: "bold",
      )[Contents]
    ]

    #v(1em)

    #outline(title: none)
  ]
}


#let render-publisher-imprint(publisher-name: "VTR Press", publisher-name-lines: ()) = {
  if publisher-name != "" {
    v(1em)
    align(center)[
      text(size: 9pt)[Published by]
      linebreak()
      #if publisher-name-lines.len() > 0 {
        for line in publisher-name-lines {
          text(size: 9pt, weight: "bold")[#line]
          linebreak()
        }
      } else {
        text(size: 9pt, weight: "bold")[#publisher-name]
      }
    ]
  }
}


#let part-page(body) = {
  plain-page[
    #body
  ]
}


#let front-matter-page(body) = {
  plain-page[
    #body
  ]
}


#let chapter-page(title, body) = {
  current-chapter-title.update(title)
  running-page[
    #body
  ]
}


#let running-section-page(title, body) = {
  current-chapter-title.update(title)
  running-page[
    #body
  ]
}

// Technical documents do not use a back cover. This function is kept
// for API parity (see render-cover above) and as a safe fallback if
// a manuscript unexpectedly includes a Back Cover section.
#let back-cover-page(body) = {
  plain-page[
    #body
  ]
}

#let render-scene-title(title) = {
  v(0.8em)

  text(weight: "bold")[#title]

  v(0.5em)
}


#let centered-front-matter(body) = {
  v(1fr)
  body
  v(1fr)
}
