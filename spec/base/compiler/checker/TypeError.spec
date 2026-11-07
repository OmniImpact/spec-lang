#! Package base:compiler:checker
#! A semantic type error: source line plus diagnostic, rendered with the
#! standard error presentation. Wraps [Error] so checker diagnostics carry
#! the same provenance story as scanner and parser diagnostics.

Class is TypeError{
	namespace: ['base', 'compiler', 'checker'];

	replace Array of Array of String is using: [
		['base', 'compiler', Error],
		['base', 'sys', as Reflection()]
	];

	## One-based source line (0 when the error is program-level).
	Int is line: 0;

	## The diagnostic message.
	String is message: '';

	## Initializes a type error.
	##
	## @param line: Source line coordinate.
	## @param message: Diagnostic text.
	replace Function is init(Int is line, String is message){
		self:line: line;
		self:message: message;
	}

	## Renders the error with its provenance.
	##
	## @return: Multi-line diagnostic text.
	replace Function of String is toString(){
		local Error is e: Error:init(message: self:message);
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: self:line, col: 0);
		return e:toString();
	}
}
