#let setup-headings(body) = {
  show heading.where(level: 1): set text(
    size: 20pt,
    weight: "bold",
  )

  // Numbered sections: only headings that participate in the outline
  // (i.e. real document sections) receive automatic numbering. Front
  // matter-style headings rendered with outlined: false are left
  // unnumbered, matching the classic theme's convention.
  //
  // A numbering function (rather than a plain "1." pattern string) is
  // used deliberately: Typst's default heading numbering counts every
  // ancestor level, and since technical documents currently use only
  // level-2 section headings (no level-1 heading precedes them), a
  // plain "1." pattern renders as "0.1.", "0.2." etc. Selecting just
  // the heading's own counter component avoids that.
  show heading.where(level: 2, outlined: true): set heading(
    numbering: (..nums) => numbering("1.", nums.pos().last()),
  )

  show heading.where(level: 2): set text(
    size: 14pt,
    weight: "bold",
  )

  show heading.where(level: 3): set text(
    size: 12pt,
    weight: "bold",
  )

  // NOTE: setup-headings takes `body` and returns it as its final
  // statement (unlike the other setup-* functions, which take no
  // arguments) so that these `show` rules and `body` share the same
  // lexical scope. See theme.typ for why this is required -- a
  // no-argument `#setup-headings()` call, as themes/classic uses,
  // does not propagate its `show` rules to sibling content.
  body
}
