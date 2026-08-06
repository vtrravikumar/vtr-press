#import "functions.typ": running-book-title


#let setup-metadata(book-title: "", book-author: "") = {
  let book_title = book-title
  let book_author = book-author

  running-book-title.update(book-title)
}
