#import "functions.typ": current-chapter-title
#import "page.typ": plain-page, running-page


#let render-cover(cover-path) = {
  set page(
    margin: 0mm,
    header: none,
    footer: none,
  )

  image(
    cover-path,
    width: 100%,
    height: 100%,
  )

  pagebreak()

  set page(
    margin: (
      x: 18mm,
      y: 22mm,
    ),
    header: none,
    footer: none,
  )
}


#let render-title-page(
  title: "",
  subtitle: "",
  author: "",
  copyright-year: "",
) = {
  plain-page()

  align(center)[
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
      #image("/assets/publisher/logo.png", width: 20mm)
      #v(2mm)
      #text(size: 11pt)[#copyright-year]
    ]
  ]

  pagebreak()
}


#let render-contents() = {
  plain-page()

  align(left)[
    #text(
      size: 22pt,
      weight: "bold",
    )[Contents]
  ]

  v(1em)

  outline(title: none)
}


#let part-page() = {
  plain-page()
}


#let front-matter-page() = {
  plain-page()
}


#let chapter-page(title) = {
  current-chapter-title.update(title)
  running-page()
}


#let running-section-page(title) = {
  current-chapter-title.update(title)
  running-page()
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
