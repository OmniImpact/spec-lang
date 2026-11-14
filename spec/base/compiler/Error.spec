#! Package base:compiler
#! A compiler diagnostic with provenance.
##
## An [Error] carries a human-readable message, a structured [SourceLocation]
## coordinate span, plus a trace of [StackFrame] entries recording where
## in the compilation it arose and how it propagated (scan -> parse -> check -> generate).
## Producers append frames as the error moves up; `toString` renders message then
## trace, innermost first, so traced output reads like a story.

Class is Error{
	replace Array of String is namespace: ['base', 'compiler'];

	replace Array of Array of String is using: [
		['base', 'sys', StackFrame],
		['base', 'sys', SourceLocation]
	];

	## The diagnostic message.
	local String is message: '';

	## The source location span.
	local SourceLocation is location;

	## Propagation provenance, innermost first.
	local Array of StackFrame is trace: [];

	## Initializes an error with its message and optional source location.
	##
	## @param message: Full diagnostic text.
	## @param location: Structured source location span.
	replace Function is init(String is message, SourceLocation is location: SourceLocation:init(file: '', line: 0, col: 0, length: 0)){
		self:message: message;
		self:location: location;
		self:trace: [];
	}

	## Appends a provenance frame carrying source coordinates.
	##
	## @param className: Name of the class that observed the error.
	## @param methodName: Name of the method that observed the error.
	## @param line: One-based line of the observation.
	## @param col: One-based column of the observation.
	Function is addTraceAt(String is className, String is methodName, Int is line, Int is col){
		self:trace:add(item: StackFrame:init(location: SourceLocation:init(file: self:location:getFile(), line: line, col: col), className: className, methodName: methodName));
	}

	## Returns the diagnostic message.
	##
	## @return: Message string.
	Function of String is getMessage(){
		return self:message;
	}

	## Returns the structured source location.
	##
	## @return: [SourceLocation] span.
	Function of SourceLocation is getLocation(){
		return self:location;
	}

	## Sets or updates the structured source location.
	##
	## @param loc: The updated source location.
	Function is setLocation(SourceLocation is loc){
		self:location: loc;
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
