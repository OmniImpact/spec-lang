#! Package base:sys
#! Public wrapper over the sysinternal compile-time source identity floor.
##
## Same-name wrapper rule: only base:sys may call base:sysinternal. In the
## transitional era the generator intercepts Reflection:class()/method()
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
}
