#! Package base:sys
#! Provides system interaction, process execution, and execution frames.

## Encapsulates source file provenance, line numbers, and column offsets.
##
## Used across compiler diagnostics, tokens, and runtime stack frames.
Class is SourceLocation{

	## File path or URI of the source file.
	local String is file: "";

	## One-based line number in source.
	local Int is line: 1;

	## One-based column number in source.
	local Int is col: 1;

	## Initializes a source location coordinate.
	##
	## @param file: The file path or URI of the source.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace local Function is init(String is file, Int is line, Int is col){
		self:file: file;
		self:line: line;
		self:col: col;
	}

	## Returns the source file path.
	##
	## @return: File path string.
	local Function of String is getFile(){
		return self:file;
	}

	## Returns the one-based line number.
	##
	## @return: Line number integer.
	local Function of Int is getLine(){
		return self:line;
	}

	## Returns the one-based column number.
	##
	## @return: Column number integer.
	local Function of Int is getCol(){
		return self:col;
	}

	## Formats the location as a standardized coordinate string.
	##
	## @return: Formatted string in "file:line:col" or "line:col" format.
	## @example:
	## ```spec
	## local String is s: loc:toString();
	## ```
	replace local Function of String is toString(){
		if (self:file:length() > 0) {
			return self:file . ":" . self:line . ":" . self:col;
		}
		return self:line . ":" . self:col;
	}

}
