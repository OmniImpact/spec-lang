#! Package base:sys
#! The lazy-evaluation provider: exposes `lazy({ ... })` via `as Lazy()`.

Class is Lazy{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sysinternal', Lazy]
	];

	## Binds a deferred initializer closure [init] that evaluates on first
	## read and caches the result.
	##
	## @param init: The initializer closure yielding the value.
	Function of Any is lazy(Function of Any is init){
		return base:sysinternal:Lazy:eval(init: init);
	}
}
