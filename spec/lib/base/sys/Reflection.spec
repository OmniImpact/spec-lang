#! Package base:sys
#! Public wrapper over the sysinternal compile-time source identity floor.
##
## Same-name wrapper rule: only base:sys may call base:sysinternal. In the
## current era the generator intercepts Reflection:class()/method()
## AT THE CALL SITE (injecting the caller's class/method as compile-time
## constants), so these bodies exist for the post-interception era when
## the wrapper becomes the only path.

Class is Reflection{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Reflection]
	];

	## The enclosing class name at the call site, injected by the generator.
	##
	## @return: The call site's class name.
	Function of String is class(){
		return base:sysinternal:Reflection:class();
	}

	## The enclosing method name at the call site, injected by the generator.
	##
	## @return: The call site's method name.
	Function of String is method(){
		return base:sysinternal:Reflection:method();
	}

	## The enclosing source file path at the call site, injected by the generator.
	##
	## @return: The call site's source file path.
	Function of String is file(){
		return base:sysinternal:Reflection:file();
	}

	## The source line number at the call site, injected by the generator.
	##
	## @return: The call site's 1-based line number.
	Function of Int is line(){
		return base:sysinternal:Reflection:line();
	}

	## True when the enclosing call's resolved type parameter T is an ARC-managed reference type.
	##
	## @return: True when the call site's type argument is ARC-managed.
	Function of Boolean is isArcTypeParam(){
		return base:sysinternal:Reflection:isArcTypeParam();
	}

	## Returns the return-type category of the closure argument at the call site
	## (`0` = scalar Int/Boolean/Byte, `1` = ARC reference, `2` = Float, `3` = Void).
	##
	## @return: Closure return kind code.
	Function of Int is closureReturnKind(){
		return base:sysinternal:Reflection:closureReturnKind();
	}
}
