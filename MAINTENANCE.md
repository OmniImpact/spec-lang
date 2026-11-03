# Spec Compiler Maintenance Guide

This document succinctly outlines the required steps and checklist whenever a new feature, syntax extension, or standard package is added to the **Spec** language.

---

## Feature Addition Checklist

### 1. Compiler Implementation
- [ ] **AST (`src/ast.rs`)**: Define any new syntax tree nodes, expressions, types, or operators.
- [ ] **Lexer (`src/lexer.rs`)**: Add new keywords, symbols, escape sequences, or literal tokenizers.
- [ ] **Parser (`src/parser.rs`)**: Implement parsing rules, operator precedence, and support for both explicit and shorthand variants.
- [ ] **Code Generator & Runtime (`src/codegen.rs`)**:
  - Add C runtime structures/functions to `runtime_prelude()`.
  - Transpile AST nodes to clean C99 code.
- [ ] **Linter (`src/linter.rs`)**:
  - Ensure the feature respects the **tab-based indentation standard**.
  - Track optional/shorthand parameter rules and warnings.

---

### 2. Test Verification (Full & Shorthand)
Every new feature must have tests demonstrating both styles:
1. **Full Explicit Syntax**: Explicit modifiers (`replace local`), full types (`Array of Int`), and named arguments (`key: "...", default: "..."`).
2. **Optional Syntax Shorthand**: Inferred/omitted modifiers, positional calls, batch array operations (`arr:add([...])`), and tab indentation.

Verification commands:
```bash
# Build the release compiler
cargo build --release

# Run the linter on test files (must report 0 warnings for standard tab files)
./spec --lint examples/my_feature.spec

# Compile and run binary
./spec -i examples/my_feature.spec -o my_feature_bin
./my_feature_bin
```

---

### 3. Kate Syntax Highlighting
Whenever keywords, types, or standard packages are introduced:
1. **Update `spec-kate.xml`**:
   - Add new keywords to `<list name="keywords">`.
   - Add new types to `<list name="types">`.
   - Add new packages/builtins to `<list name="std_packages">`.
   - Add new operators or delimiters to the respective `<AnyChar>` rules.
2. **Reinstall syntax definitions**:
   ```bash
   ./install-kate-syntax.sh
   ```
   *Deploys to `~/.local/share/org.kde.syntax-highlighting/syntax/spec.xml` and `~/.local/share/katepart5/syntax/spec.xml`.*

---

### 4. Documentation Updates
- [ ] **[docs/README.md](docs/README.md)**: Document new language grammar, operators, and syntax examples (contrasting full vs. shorthand).
- [ ] **[docs/packages.md](docs/packages.md)**: Document new packages, classes, methods, signatures, and runtime behavior.
- [ ] **[TASKS.md](TASKS.md)**: Update task status (`$` for completed items).
