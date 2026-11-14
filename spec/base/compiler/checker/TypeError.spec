#! Package base:compiler:checker
#! A semantic type error: source location span plus diagnostic, rendered with the
#! standard error presentation. Wraps [Error] so checker diagnostics carry
#! the same provenance story as scanner and parser diagnostics.

Class is TypeError{
	namespace: ['base', 'compiler', 'checker'];

	replace Array of Array of String is using: [
		['base', 'compiler', Error],
		['base', 'sys', SourceLocation],
		['base', 'sys', as Reflection()]
	];

	## One-based source line (0 when the error is program-level).
	Int is line: 0;

	## One-based source column (0 when unspecified).
	Int is col: 0;

	## Span length in characters (0 when unspecified).
	Int is length: 0;

	## Source file path (empty string when unspecified).
	String is file: '';

	## The diagnostic message.
	String is message: '';

	## Initializes a type error with coordinates and message.
	##
	## @param line: Source line coordinate.
	## @param message: Diagnostic text.
	## @param col: Optional source column coordinate.
	## @param length: Optional span length in characters.
	## @param file: Optional source file path.
	replace Function is init(Int is line, String is message, Int is col: 0, Int is length: 0, String is file: ''){
		self:line: line;
		self:message: message;
		self:col: col;
		self:length: length;
		self:file: file;
	}

	## Returns the structured source location span.
	##
	## @return: [SourceLocation] span.
	Function of SourceLocation is getLocation(){
		return SourceLocation:init(file: self:file, line: self:line, col: self:col, length: self:length);
	}

	## Renders the error with its provenance.
	##
	## @return: Multi-line diagnostic text.
	replace Function of String is toString(){
		local Error is e: Error:init(message: self:message, location: self:getLocation());
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: self:line, col: self:col);
		return e:toString();
	}
}
