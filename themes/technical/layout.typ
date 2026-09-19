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
      #v(20%)

      #text(size: 24pt, weight: "bold")[#title]

      #if subtitle != "" {
        v(0pt)
        text(size: 13pt)[#subtitle]
      }

      #v(12%)

      #if authors.len() > 0 {
        for author in authors {
          text(size: 13pt)[#author]
          linebreak()
        }
      } else {
        text(size: 13pt)[#author]
      }

      #v(20%)

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
        text(size: 10pt)[#copyright-year]
      ]
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
