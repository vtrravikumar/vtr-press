#import "functions.typ": running-header, running-footer


#let setup-page() = {
  set page(
    paper: "a5",
    margin: (
      x: 18mm,
      y: 22mm,
    ),
    numbering: none,
  )
}


#let plain-page() = {
  set page(
    header: none,
    footer: none,
  )
}


#let running-page() = {
  set page(
    header: running-header(),
    footer: running-footer(),
  )
}


#let start-main-matter() = {
  set page(
    numbering: "1",
    header: running-header(),
    footer: running-footer(),
  )
  counter(page).update(1)
}

