#! Package base:sys
#! Public wrapper over the sysinternal compile-time source identity floor.
##
## Same-name wrapper rule: only base:sys may call base:sysinternal. In the
## current era the generator intercepts Reflection:class()/method()
## AT THE CALL SITE (injecting the caller's class/method as compile-time
## constants), so these bodies exist for the post-interception era when
## the wrapper becomes the only path.

Class is Reflection{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
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
}
