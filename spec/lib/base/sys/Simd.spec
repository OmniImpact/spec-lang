#! Package base:sys
#! Portable 4-wide double-precision (`<4 x double>`) SIMD primitives backed by LLVM vector IR.

Class is Simd{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sysinternal', Simd]
	];

	## Stores 4 copies of [val] at [dst].
	Function is fill4(Int is dst, Float is val){
		base:sysinternal:Simd:fill4(dst: dst, val: val);
	}

	## Computes `dst[0..3] = a[0..3] + b[0..3]`.
	Function is add4(Int is dst, Int is a, Int is b){
		base:sysinternal:Simd:add4(dst: dst, a: a, b: b);
	}

	## Computes `dst[0..3] = a[0..3] - b[0..3]`.
	Function is sub4(Int is dst, Int is a, Int is b){
		base:sysinternal:Simd:sub4(dst: dst, a: a, b: b);
	}

	## Computes `dst[0..3] = a[0..3] * b[0..3]`.
	Function is mul4(Int is dst, Int is a, Int is b){
		base:sysinternal:Simd:mul4(dst: dst, a: a, b: b);
	}

	## Computes `dst[0..3] = a[0..3] * scalar`.
	Function is scale4(Int is dst, Int is a, Float is scalar){
		base:sysinternal:Simd:scale4(dst: dst, a: a, scalar: scalar);
	}

	## Computes `dst[0..3] = a[0..3] * b[0..3] + c[0..3]`.
	Function is fma4(Int is dst, Int is a, Int is b, Int is c){
		base:sysinternal:Simd:fma4(dst: dst, a: a, b: b, c: c);
	}

	## Computes the 4-lane dot product `sum(a[0..3] * b[0..3])`.
	Function of Float is dot4(Int is a, Int is b){
		return base:sysinternal:Simd:dot4(a: a, b: b);
	}

	## Clamps `a[0..3]` to `[lo, hi]` and writes to `dst[0..3]`.
	Function is clamp4(Int is dst, Int is a, Float is lo, Float is hi){
		base:sysinternal:Simd:clamp4(dst: dst, a: a, lo: lo, hi: hi);
	}

	## Computes `dst[0..3] = a[0..3] * scalar + c[0..3]`.
	Function is axpy4(Int is dst, Int is a, Float is scalar, Int is c){
		base:sysinternal:Simd:axpy4(dst: dst, a: a, scalar: scalar, c: c);
	}

	## Returns the horizontal sum `a[0] + a[1] + a[2] + a[3]`.
	Function of Float is sum4(Int is a){
		return base:sysinternal:Simd:sum4(a: a);
	}

	## Computes `dst[0..3] = sqrt(a[0..3])`.
	Function is sqrt4(Int is dst, Int is a){
		base:sysinternal:Simd:sqrt4(dst: dst, a: a);
	}

	## Computes `dst[0..3] = abs(a[0..3])`.
	Function is abs4(Int is dst, Int is a){
		base:sysinternal:Simd:abs4(dst: dst, a: a);
	}

	## Computes `dst[0..3] = min(a[0..3], b[0..3])`.
	Function is min4(Int is dst, Int is a, Int is b){
		base:sysinternal:Simd:min4(dst: dst, a: a, b: b);
	}

	## Computes `dst[0..3] = max(a[0..3], b[0..3])`.
	Function is max4(Int is dst, Int is a, Int is b){
		base:sysinternal:Simd:max4(dst: dst, a: a, b: b);
	}
}
