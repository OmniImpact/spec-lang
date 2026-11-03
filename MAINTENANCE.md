# Spec Compiler Maintenance Guide

This document succinctly outlines the required steps and checklist whenever a new feature, syntax extension, or standard package is added to the **Spec** language.

---

## Feature Addition Checklist

### 1. Pure-Spec Compiler Implementation
Spec is now self-hosted. Feature additions must be made directly in the pure-Spec compiler files under `lib/compiler/`:
- [ ] **AST (`lib/compiler/AST.spec`)**: Define new AST node classes, expression kinds, and statement representations.
- [ ] **Token & Lexer (`lib/compiler/Token.spec`, `lib/compiler/Lexer.spec`)**: Add token kinds, keywords, escape characters, or symbols.
- [ ] **Parser (`lib/compiler/Parser.spec`)**: Implement recursive-descent grammar rules and shorthand forms.
- [ ] **Type Checker (`lib/compiler/TypeChecker.spec`)**: Semantic validation, interface contracts, and type resolution.
- [ ] **Code Generation & Runtime**:
  - `lib/compiler/DeclarationGenerator.spec`: Struct layout, enum definitions, and forward declarations.
  - `lib/compiler/BuiltinCallGenerator.spec`: Standard library and runtime builtin call emitter.
  - `lib/compiler/CodeGenerator.spec`: Expression, statement, method, and translation unit emission.
  - `lib/compiler/RuntimePrelude.spec`: Thread-safe C11 runtime structures, helper functions, and recursive mutex locks.
- [ ] **Linter (`lib/compiler/Linter.spec`)**: Update tab indentation checks, optional parameter analysis, and coding style rules.
- [ ] **Bootstrap C Update**: Converge across 3 self-hosting stages and update `bootstrap/spec.c`:
  ```bash
  ./spec -i lib/compiler/Driver.spec -o spec-stage1
  ./spec-stage1 -i lib/compiler/Driver.spec -o spec-stage2 --emit-c /tmp/stage2.c
  ./spec-stage2 -i lib/compiler/Driver.spec -o spec-stage3 --emit-c /tmp/stage3.c
  diff -s /tmp/stage2.c /tmp/stage3.c
  cp spec-stage3 spec && cp /tmp/stage3.c bootstrap/spec.c
  ./bootstrap.sh
  ```

---

### 2. Test Verification (Full & Shorthand)
Every new feature must have tests demonstrating both styles:
1. **Full Explicit Syntax**: Explicit modifiers (`replace local`), full types (`Array of Int`), and named arguments (`key: "...", default: "..."`).
2. **Optional Syntax Shorthand**: Inferred/omitted modifiers, positional calls, batch array operations (`arr:add([...])`), and tab indentation.

Verification commands:
```bash
# Run the pure-Spec linter (must report 0 warnings for standard tab files)
./spec --lint examples/my_feature.spec

# Compile and run binary with self-hosted compiler
./spec -i examples/my_feature.spec -o my_feature_bin
./my_feature_bin
```

---

### 3. Kate Syntax Highlighting
Whenever keywords, types, or standard packages are introduced:
1. **Update `utilities/spec-kate.xml`**:
   - Add new keywords to `<list name="keywords">`.
   - Add new types to `<list name="types">`.
   - Add new packages/builtins to `<list name="std_packages">`.
   - Add new operators or delimiters to the respective `<AnyChar>` rules.
2. **Reinstall syntax definitions**:
   ```bash
   ./utilities/install-kate-syntax.sh
   ```
   *Deploys to `~/.local/share/org.kde.syntax-highlighting/syntax/spec.xml` and `~/.local/share/katepart5/syntax/spec.xml`.*

---

### 4. Documentation Updates
- [ ] **[docs/README.md](docs/README.md)**: Main portal update if new documentation categories are added.
- [ ] **[docs/language/README.md](docs/language/README.md)**: Document new language grammar, operators, and syntax examples.
- [ ] **[docs/packages/README.md](docs/packages/README.md)**: Document new packages, classes, methods, signatures, and runtime behavior.
- [ ] **[docs/tooling/README.md](docs/tooling/README.md)**: Document compiler flags, linter checks, and tooling changes.
- [ ] **[TASKS.md](TASKS.md)**: Update task status (`$` for completed items).
