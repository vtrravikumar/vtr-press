#import "functions.typ": running-header, running-footer


#let print-mode = sys.inputs.at("print-mode", default: "false") == "true"
#let page-width = if print-mode { 128.524mm } else { 148mm }
#let page-height = if print-mode { 198.374mm } else { 210mm }


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
