#! Package base:sysinternal
#! Portable 4-wide double-precision (`<4 x double>`) SIMD intrinsics lowered to LLVM vector IR.
##
## Only `base:sys:Simd` may call this floor class directly.

Class is Simd{
	replace [String] is namespace: ['base', 'sysinternal'];

	Function of Float is loadF64(Int is ptr, Int is byteOffset);
	Function is storeF64(Int is ptr, Int is byteOffset, Float is val);
	Function is fill4(Int is dst, Float is val);
	Function is add4(Int is dst, Int is a, Int is b);
	Function is sub4(Int is dst, Int is a, Int is b);
	Function is mul4(Int is dst, Int is a, Int is b);
	Function is scale4(Int is dst, Int is a, Float is scalar);
	Function is fma4(Int is dst, Int is a, Int is b, Int is c);
	Function of Float is dot4(Int is a, Int is b);
	Function is clamp4(Int is dst, Int is a, Float is lo, Float is hi);
}
