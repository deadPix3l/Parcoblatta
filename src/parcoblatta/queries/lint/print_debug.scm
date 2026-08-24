; Flags print(...) calls left in code.
((block
  (expression_statement
    (call function: (identifier) @targeta))) @contextual
 (#eq? @targeta "print")
 (#set! name "print-debug")
 (#set! message "avoid committed print() debugging")
 (#set! why "print() writes directly to stdout and is easy to leave behind accidentally.")
 (#set! help "Use logging, structured output, or remove the debug statement."))

((module
  (expression_statement
    (call function: (identifier) @targeta))) @contextual
 (#eq? @targeta "print")
 (#set! name "print-debug")
 (#set! message "avoid committed print() debugging")
 (#set! why "print() writes directly to stdout and is easy to leave behind accidentally.")
 (#set! help "Use logging, structured output, or remove the debug statement."))
