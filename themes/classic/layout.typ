#import "functions.typ": current-chapter-title, running-footer
#import "page.typ": plain-page, running-page


#let render-cover(cover-path) = {
  set page(
    paper: "a5",
    margin: 0mm,
    numbering: none,
    header: none,
    footer: none,
  )

  image(
    cover-path,
    width: 100%,
    height: 100%,
  )
}


#let render-title-page(
  title: "",
  subtitle: "",
  author: "",
  copyright-year: "",
  show-publisher-logo: true,
) = {
  plain-page[
    #align(center)[
      #v(20%)

      #text(size: 28pt, weight: "bold")[#title]

      #if subtitle != "" {
        v(0pt)
        text(size: 15pt)[#subtitle]
      }

      #v(12%)

      #text(size: 16pt)[#author]

      #v(20%)

      #align(center)[
        #if show-publisher-logo {
          image("/assets/publisher/logo.png", width: 20mm)
          v(2mm)
        }
        #text(size: 11pt)[#copyright-year]
      ]
    ]
  ]
}


#let render-contents() = {
  plain-page[
    #align(left)[
      #text(
        size: 22pt,
        weight: "bold",
      )[Contents]
    ]

    #v(1em)

    #outline(title: none)
  ]
}


#let render-publisher-imprint() = {
  v(1em)
  align(center)[
    #text(size: 10pt)[Published by]
    #linebreak()
    #text(size: 10pt, weight: "bold")[VTR Press]
  ]
}


#let part-page(body) = {
  plain-page[
    #body
  ]
}


#let print-part-page(body) = {
  set page(
    paper: "a5",
    margin: (
      x: 18mm,
      y: 22mm,
    ),
    numbering: "1",
    header: none,
    footer: running-footer(),
  )

  body
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

#let back-cover-page(body) = {
  plain-page[
    #body
  ]
}


#let blank-recto-pagebreak() = {
  set page(
    paper: "a5",
    margin: (
      x: 18mm,
      y: 22mm,
    ),
    numbering: none,
    header: none,
    footer: none,
  )

  pagebreak(to: "odd")
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
