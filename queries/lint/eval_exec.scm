; Flags eval(...) and exec(...) calls.
((block
  (expression_statement
    (call function: (identifier) @target))) @context
 (#match? @target "^(eval|exec)$")
 (#set! name "dynamic-exec")
 (#set! message "avoid eval() and exec()")
 (#set! why "Executing dynamic code is difficult to audit and can create security vulnerabilities.")
 (#set! help "Use explicit parsing, dispatch tables, or safer domain-specific evaluation instead."))

((module
  (expression_statement
    (call function: (identifier) @target))) @context
 (#match? @target "^(eval|exec)$")
 (#set! name "dynamic-exec")
 (#set! message "avoid eval() and exec()")
 (#set! why "Executing dynamic code is difficult to audit and can create security vulnerabilities.")
 (#set! help "Use explicit parsing, dispatch tables, or safer domain-specific evaluation instead."))
