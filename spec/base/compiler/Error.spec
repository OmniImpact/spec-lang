#! Package base:compiler
#! A compiler diagnostic with provenance.
##
## An [Error] carries a human-readable message plus a trace of [StackFrame]
## entries recording where in the compilation it arose and how it
## propagated (scan -> parse -> check -> generate). Producers append frames
## as the error moves up; `toString` renders message then trace, innermost
## first, so traced output reads like a story.

Class is Error{
	replace Array of String is namespace: ['base', 'compiler'];

	replace Array of Array of String is using: [
		['base', 'sys', StackFrame]
,
		['base', 'sys', SourceLocation]
	];

	## The diagnostic message (position information included by the
	## producer; it knows the source coordinates).
	local String is message: '';

	## Propagation provenance, innermost first.
	local Array of StackFrame is trace: [];

	## Initializes an error with its message.
	##
	## @param message: Full diagnostic text.
	replace Function is init(String is message){
		self:message: message;
		self:trace: [];
	}

	## Appends a provenance frame carrying source coordinates — the form
	## producers closest to the source use (scanners and parsers know the
	## exact position where an error was detected).
	##
	## @param className: Name of the class that observed the error.
	## @param methodName: Name of the method that observed the error.
	## @param line: One-based line of the observation.
	## @param col: One-based column of the observation.
	Function is addTraceAt(String is className, String is methodName, Int is line, Int is col){
		self:trace:add(item: StackFrame:init(location: SourceLocation:init(file: '', line: line, col: col), className: className, methodName: methodName));
	}

	## Returns the diagnostic message.
	##
	## @return: Message string.
	Function of String is getMessage(){
		return self:message;
	}

	## Returns the propagation trace.
	##
	## @return: [StackFrame] entries, innermost first.
	Function of Array of StackFrame is getTrace(){
		return self:trace;
	}

	## Renders message then trace lines, innermost first.
	##
	## @return: Multi-line diagnostic text.
	replace Function of String is toString(){
		local String is out: self:message;
		self:trace:each(action: local Function(StackFrame is f){
			out: out . String:newline() . "  at " . f:toString();
		});
		return out;
	}
}
