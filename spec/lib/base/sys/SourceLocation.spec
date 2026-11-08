#! Package base:sys
#! System interaction, process execution, and execution frames.

## Encapsulates source file provenance, line numbers, and column offsets.
##
## Used across compiler diagnostics, tokens, and runtime stack frames.

Class is SourceLocation{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
];

	## File path or URI of the source file.
	local String is file: '';

	## One-based line number in source.
	local Int is line: 1;

	## One-based column number in source.
	local Int is col: 1;

	## Initializes a source location coordinate.
	##
	## @param file: The file path or URI of the source.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace Function is init(String is file, Int is line, Int is col){
		self:file: file;
		self:line: line;
		self:col: col;
	}

	## Returns the source file path.
	##
	## @return: File path string.
	Function of String is getFile(){
		return self:file;
	}

	## Returns the one-based line number.
	##
	## @return: Line number.
	Function of Int is getLine(){
		return self:line;
	}

	## Returns the one-based column number.
	##
	## @return: Column number.
	Function of Int is getCol(){
		return self:col;
	}

	## Formats the location as a standardized coordinate string.
	##
	## @return: "file:line:col", or "line:col" when no file is recorded.
	replace Function of String is toString(){
		local String is f: self:file;
		Conditional:branch(check: { f:length() > 0 }, then: {
			return f . ':' . (self:line as String) . ':' . (self:col as String);
		});
		return (self:line as String) . ':' . (self:col as String);
	}
}
