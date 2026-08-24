; Flags assert statements in application code.
((block
  (assert_statement) @target) @context
 (#set! name "assert-statement")
 (#set! message "avoid assert for runtime validation")
 (#set! why "Python can remove assert statements when optimization is enabled with -O.")
 (#set! help "Raise an explicit exception for runtime validation; reserve assert for internal invariants/tests."))

((module
  (assert_statement) @target) @context
 (#set! name "assert-statement")
 (#set! message "avoid assert for runtime validation")
 (#set! why "Python can remove assert statements when optimization is enabled with -O.")
 (#set! help "Raise an explicit exception for runtime validation; reserve assert for internal invariants/tests."))
