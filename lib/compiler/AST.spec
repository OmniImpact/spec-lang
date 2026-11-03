#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Compiler facade re-exporting [base:reflect] and [base:meta] AST models.
class AST{

	replace local Array of String is using: [
		base:reflect:*,
		base:meta:*
	];

}
