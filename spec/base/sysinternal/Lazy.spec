#! Package base:sysinternal
#! The lazy-evaluation floor primitive.

Class is Lazy{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Evaluates [init] lazily on first read of the bound field or local.
	##
	## @param init: The initializer closure yielding the value.
	Function of Any is eval(Function of Any is init);
}
