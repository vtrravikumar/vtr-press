#import "functions.typ": running-header, running-footer


#let page-width = 148mm
#let page-height = 210mm


#let setup-page() = {
  set page(
    width: page-width,
    height: page-height,
    margin: (
      inside: 20mm,
      outside: 15mm,
      top: 22mm,
      bottom: 22mm,
    ),
    numbering: none,
  )
}


#let plain-page(body) = {
  set page(
    width: page-width,
    height: page-height,
    margin: (
      inside: 20mm,
      outside: 15mm,
      top: 22mm,
      bottom: 22mm,
    ),
    numbering: none,
    header: none,
    footer: none,
  )

  body
}


#let running-page(body) = {
  set page(
    width: page-width,
    height: page-height,
    margin: (
      inside: 20mm,
      outside: 15mm,
      top: 22mm,
      bottom: 22mm,
    ),
    header: running-header(),
    footer: running-footer(),
  )

  body
}


#let main-matter(body) = {
  set page(
    width: page-width,
    height: page-height,
    margin: (
      inside: 20mm,
      outside: 15mm,
      top: 22mm,
      bottom: 22mm,
    ),
    numbering: "1",
    header: running-header(),
    footer: running-footer(),
  )
  counter(page).update(1)

  body
}
