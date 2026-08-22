; Flags bare except: blocks.
((try_statement
  (except_clause) @targeta) @context
 (#not-match? @targeta "^except\\s+[^:]+:")
 (#set! name "bare-except")
 (#set! message "avoid bare except")
 (#set! why "Bare except catches BaseException, including KeyboardInterrupt and SystemExit.")
 (#set! help "Catch a specific exception type, or use 'except Exception:' if that is truly intended."))
