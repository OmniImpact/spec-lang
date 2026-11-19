#! Package base:compiler:checker
#! Canonical type-domain operations for the Spec type checker.
#! Centralizes base-name extraction, generic container queries, function
#! return-type extraction, and canonical type construction so the checker
#! never scatters ad-hoc colon-splitting or prefix slicing across passes.

Class is TypeDomain{
	namespace: ['base', 'compiler', 'checker'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Extracts the base type name from a canonical or source-form type string
	## (e.g. `'Array:Int'` -> `'Array'`, `'Map of String to Int'` -> `'Map'`,
	## `'Outer:Inner'` stays intact when no generic separator applies? Note: for
	## generic containers/classes this returns the first segment before `:` or ` of `).
	Function of String is baseName(String is t){
		if({ t == '' }, { return ''; });
		local Int is cIdx: t:indexOf(search: ':', default: -1);
		local Int is ofIdx: t:indexOf(search: ' of ', default: -1);
		if({ cIdx >= 0 && (ofIdx < 0 || cIdx < ofIdx) }, {
			return t:substring(start: 0, end: cIdx);
		});
		if({ ofIdx >= 0 }, {
			return t:substring(start: 0, end: ofIdx);
		});
		return t;
	}

	## True when [t] is [base] or a parameterized form of [base] (`base:...` or `base of ...`).
	Function of Boolean is isOfBase(String is t, String is base){
		if({ t == base }, { return true; });
		if({ t:startsWith(prefix: base . ':') }, { return true; });
		if({ t:startsWith(prefix: base . ' of ') }, { return true; });
		return false;
	}

	## True when [t] is a parameterized form of [base] (`base:...` or `base of ...`).
	Function of Boolean is isParameterized(String is t, String is base){
		return t:startsWith(prefix: base . ':') || t:startsWith(prefix: base . ' of ');
	}

	## True when [t] is an Array, List, or Map type (bare or parameterized).
	Function of Boolean is isContainer(String is t){
		return :isOfBase(t: t, base: 'Array') || :isOfBase(t: t, base: 'List') || :isOfBase(t: t, base: 'Map');
	}

	## True when [t] is a Function type (bare or with return type).
	Function of Boolean is isFunction(String is t){
		return t == 'Function' || t:startsWith(prefix: 'Function:') || t:startsWith(prefix: 'Function of ');
	}

	## True when [t] is a Function type carrying an explicit return type (`Function:R`).
	Function of Boolean is hasFunctionReturn(String is t){
		return (t:startsWith(prefix: 'Function:') && t:length() > 9) || (t:startsWith(prefix: 'Function of ') && t:length() > 12);
	}

	## Extracts the return type from `Function:R` or `Function of R`, or [default] if untyped.
	Function of String is functionReturn(String is t, String is default: ''){
		if({ t:startsWith(prefix: 'Function:') && t:length() > 9 }, {
			return t:substring(start: 9, end: t:length());
		});
		if({ t:startsWith(prefix: 'Function of ') && t:length() > 12 }, {
			return t:substring(start: 12, end: t:length());
		});
		return default;
	}

	## Extracts the single element type from a 1-arg generic (`Array:X`, `List:X`, `Flow:X`,
	## or their ` of ` forms), or `''` if bare/unparameterized.
	Function of String is elemType(String is t){
		local Int is cIdx: t:indexOf(search: ':', default: -1);
		local Int is ofIdx: t:indexOf(search: ' of ', default: -1);
		if({ cIdx >= 0 && (ofIdx < 0 || cIdx < ofIdx) && cIdx + 1 < t:length() }, {
			return t:substring(start: cIdx + 1, end: t:length());
		});
		if({ ofIdx >= 0 && ofIdx + 4 < t:length() }, {
			return t:substring(start: ofIdx + 4, end: t:length());
		});
		return '';
	}

	## Extracts the key type from a Map type (`Map:K:V` or `Map of K to V`), or `''`.
	Function of String is mapKeyType(String is t){
		if({ t:startsWith(prefix: 'Map:') && t:length() > 4 }, {
			local String is rest: t:substring(start: 4, end: t:length());
			local Int is sep: rest:indexOf(search: ':', default: -1);
			if({ sep > 0 }, {
				return rest:substring(start: 0, end: sep);
			});
			return rest;
		});
		if({ t:startsWith(prefix: 'Map of ') && t:length() > 7 }, {
			local String is rest: t:substring(start: 7, end: t:length());
			local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
			if({ toIdx > 0 }, {
				return rest:substring(start: 0, end: toIdx);
			});
		});
		return '';
	}

	## Extracts the value type from a Map type (`Map:K:V` or `Map of K to V`),
	## preserving nested generic value types (e.g. `Map:String:Array:Int` -> `Array:Int`).
	Function of String is mapValType(String is t){
		if({ t:startsWith(prefix: 'Map:') && t:length() > 4 }, {
			local String is rest: t:substring(start: 4, end: t:length());
			local Int is sep: rest:indexOf(search: ':', default: -1);
			if({ sep >= 0 && sep + 1 < rest:length() }, {
				return rest:substring(start: sep + 1, end: rest:length());
			});
		});
		if({ t:startsWith(prefix: 'Map of ') && t:length() > 7 }, {
			local String is rest: t:substring(start: 7, end: t:length());
			local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
			if({ toIdx >= 0 && toIdx + 4 < rest:length() }, {
				return rest:substring(start: toIdx + 4, end: rest:length());
			});
		});
		return '';
	}

	## Canonical constructors for parameterized type keys.
	Function of String is makeArray(String is elem){
		if({ elem == '' }, { return 'Array'; });
		return ('Array:' . elem):intern();
	}

	Function of String is makeMap(String is key, String is val){
		if({ key == '' || val == '' }, { return 'Map'; });
		return ('Map:' . key . ':' . val):intern();
	}

	Function of String is makeFunction(String is ret){
		if({ ret == '' || ret == 'Void' }, { return 'Function'; });
		return ('Function:' . ret):intern();
	}

	Function of String is makeFlow(String is elem){
		if({ elem == '' }, { return 'Flow'; });
		return ('Flow:' . elem):intern();
	}
}
