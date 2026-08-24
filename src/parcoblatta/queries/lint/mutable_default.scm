; Flags mutable default argument values like def f(x=[]).
((function_definition
  name: (identifier) @context
  parameters: (parameters
    (default_parameter
      name: (identifier) @context
      value: [(list) (dictionary) (set)] @target))) @context
 (#set! name "mutable-default")
 (#set! message "avoid mutable default argument")
 (#set! why "Default argument objects are created once at function definition time and reused across calls.")
 (#set! help "Use None as the default and create a new list/dict/set inside the function."))
