#! Package base:sys
#! Provides system interaction, process execution, and execution frames.

## Represents an execution frame within a runtime call stack or error trace.
Class is StackFrame{

	replace Array of String is using: [
		base:sys:SourceLocation
	];

	## Source coordinate of this call frame.
	local SourceLocation is location;

	## Enclosing class name (empty if standalone function).
	local String is className: '';

	## Method or function name of this frame.
	local String is methodName: '';

	## Initializes a stack frame.
	##
	## @param location: The source location where invocation occurred.
	## @param className: Name of the enclosing class.
	## @param methodName: Name of the executed method.
	replace Function is init(SourceLocation is location, String is className, String is methodName){
		self:location: location;
		self:className: className;
		self:methodName: methodName;
	}

	## Returns the source coordinate of this frame.
	##
	## @return: [SourceLocation] instance.
	local Function of SourceLocation is getLocation(){
		return self:location;
	}

	## Returns the enclosing class name.
	##
	## @return: ClassInfo name string.
	Function of String is getClassName(){
		return self:className;
	}

	## Returns the method name.
	##
	## @return: Method name string.
	Function of String is getMethodName(){
		return self:methodName;
	}

	## Formats the frame as a standardized stack trace line.
	##
	## @return: Formatted string in "ClassInfo:method (file:line:col)" format.
	replace Function of String is toString(){
		local String is locStr: '';
		if (self:location:getLine() > 0) {
			locStr: ' (' . self:location:toString() . ')';
		}
		if (self:className:length() > 0) {
			return self:className . ':' . self:methodName . locStr;
		}
		return self:methodName . locStr;
	}

}
