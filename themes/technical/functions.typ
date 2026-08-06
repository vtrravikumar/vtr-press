#let running-book-title = state("running-book-title", "")
#let current-chapter-title = state("current-chapter-title", "")


#let running-header() = context {
  let page-number = here().page()
  let chapter-opening = query(heading.where(level: 2)).any(
    it => it.location().page() == page-number
  )

  if not chapter-opening {
    align(center)[
      #text(size: 9pt, tracking: 0.5pt)[
        #if calc.even(page-number) {
          upper(running-book-title.get())
        } else {
          upper(current-chapter-title.get())
        }
      ]
    ]
  }
}


#let running-footer() = context {
  align(center)[
    #text(size: 9pt)[#counter(page).display()]
  ]
}
