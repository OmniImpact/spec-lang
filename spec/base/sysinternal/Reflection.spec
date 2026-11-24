#! Package base:sysinternal
#! Compile-time source identity.
##
## Interface-style declarations whose implementations the GENERATOR
## provides: a call injects the enclosing class or method name of the call
## site as a compile-time constant — no runtime lookup, no arguments.
## Unlike the C-floor classes here (bound by the spec_<snake> naming
## convention), these bind to generator-injected constants; both are
## implementation-environment bindings only Spec source cannot express.

Class is Reflection{
	replace [String] is namespace: ['base', 'sysinternal'];

	## The enclosing class name at the call site, injected by the generator.
	##
	## @return: The call site's class name.
	Function of String is class();

	## The enclosing method name at the call site, injected by the generator.
	##
	## @return: The call site's method name.
	Function of String is method();

	## The enclosing source file path at the call site, injected by the generator.
	##
	## @return: The call site's source file path.
	Function of String is file();

	## The source line number at the call site, injected by the generator.
	##
	## @return: The call site's 1-based line number.
	Function of Int is line();
}
