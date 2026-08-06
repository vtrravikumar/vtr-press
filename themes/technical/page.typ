#import "functions.typ": running-header, running-footer


#let setup-page() = {
  set page(
    paper: "a4",
    margin: (
      x: 25mm,
      y: 25mm,
    ),
    numbering: none,
  )
}


#let plain-page(body) = {
  set page(
    paper: "a4",
    margin: (
      x: 25mm,
      y: 25mm,
    ),
    numbering: none,
    header: none,
    footer: none,
  )

  body
}


#let running-page(body) = {
  set page(
    paper: "a4",
    margin: (
      x: 25mm,
      y: 25mm,
    ),
    header: running-header(),
    footer: running-footer(),
  )

  body
}


#let main-matter(body) = {
  set page(
    paper: "a4",
    margin: (
      x: 25mm,
      y: 25mm,
    ),
    numbering: "1",
    header: running-header(),
    footer: running-footer(),
  )
  counter(page).update(1)

  body
}
