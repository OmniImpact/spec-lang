# Spec Compiler Tasks

$ Initialize Cargo project for `spec` compiler
$ Implement Lexer and Parser for Spec language
$ Implement C Code Generator and C Runtime
$ Implement CLI driver for `spec -i <input> -o <output>`
$ Verify `helloworld.spec` compiles to `helloworldspec` and runs with `--name Daniel`
$ Add distinction between single-quote (literal) and double-quote (escaped whitespace chars) strings
$ Add support for primitive types Int and Float, plus float literals
$ Add basic math operators (+, -, *, /, %) with operator precedence and grouping
$ Add Array to base:struct runtime with creation, length, get, and append
$ Add base:math package with round, floor, ceil/ceiling, and random functions
$ Write comprehensive test program demonstrating strings, math, arrays, and base:math
$ Create docs/ folder and write comprehensive markdown documentation for language features and packages
$ Create spec-kate.xml syntax highlighting file for Kate and installation bash script
$ Support array arguments in Array add method (appending multiple items from an array)
$ Add linter feature to spec compiler (CLI flag --lint) detecting space-based indentation and optional parameters
$ Create examples/blackjack_shorthand.spec showcasing cleaner shorthand and optional syntax with tabs
$ Create MAINTENANCE.md detailing checklist for future feature additions
$ Extend Lexer & Parser with `extends`, `if`/`else`, `return`, comparisons, logicals, and shorthand method syntax
$ Support internal/nested classes in AST, Parser, and Code Generator
$ Implement variable & field reassignment, return statements, and instantiation via Class:init(...)
$ Implement While:run loop runner and Input:prompt in C runtime
$ Verify both examples/blackjack.spec and examples/blackjack_shorthand.spec compile and run
$ Implement multi-file package/module loader in compiler resolving `using` paths to `.spec` files
$ Add standard library directory `lib/` and implement Spec packages in `.spec` files
$ Implement any required compiler primitives or operations to support Spec-implemented packages
$ Verify multi-file compilation and execution across all test suites
$ Update documentation and MAINTENANCE.md with multi-file and package guidelines
$ Implement character-level String inspection methods (length, charAt, substring, indexOf, isDigit, isAlpha, isWhitespace)
$ Implement base:io:File in Spec and C runtime with read, write, and exists
$ Implement base:sys:Process in Spec and C runtime with execute(command, args)
$ Create test program examples/phase1_test.spec and verify compilation and execution
$ Update Kate syntax highlighting, documentation, and commit Phase 1 as v0.000.003
$ Implement extended Array methods in C runtime and lib/base/struct/Array.spec (pop, removeAt, slice, clear, indexOf)
$ Implement extended Map methods in C runtime and lib/base/struct/Map.spec (set, has, remove, keys, length)
$ Create comprehensive Phase 2 test suite in examples/phase2_test.spec and verify
$ Update documentation and commit Phase 2 as v0.000.004
