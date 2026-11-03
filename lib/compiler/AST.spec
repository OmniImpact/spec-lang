#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Compiler facade re-exporting [base:reflect] and [base:meta] AST models.
Class is AST{

	replace local Array of String is using: [
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*
	];

}
