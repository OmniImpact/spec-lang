#! Package base:sysinternal
#! The math floor: hardware-accelerated libm primitives, IEEE-754 conversions,
#! and lock-free thread-local PRNG bound to C by the naming convention.

Class is Math{
	namespace: ['base', 'sysinternal'];

	## Square root. Bound to `spec_math_sqrt`.
	Function of Float is math_sqrt(Float is v);

	## Cube root. Bound to `spec_math_cbrt`.
	Function of Float is math_cbrt(Float is v);

	## Sine (radians). Bound to `spec_math_sin`.
	Function of Float is math_sin(Float is v);

	## Cosine (radians). Bound to `spec_math_cos`.
	Function of Float is math_cos(Float is v);

	## Tangent (radians). Bound to `spec_math_tan`.
	Function of Float is math_tan(Float is v);

	## Arc sine (radians). Bound to `spec_math_asin`.
	Function of Float is math_asin(Float is v);

	## Arc cosine (radians). Bound to `spec_math_acos`.
	Function of Float is math_acos(Float is v);

	## Arc tangent (radians). Bound to `spec_math_atan`.
	Function of Float is math_atan(Float is v);

	## Two-argument arc tangent (radians). Bound to `spec_math_atan2`.
	Function of Float is math_atan2(Float is y, Float is x);

	## Natural exponential e^v. Bound to `spec_math_exp`.
	Function of Float is math_exp(Float is v);

	## Natural logarithm ln(v). Bound to `spec_math_log`.
	Function of Float is math_log(Float is v);

	## Base-2 logarithm. Bound to `spec_math_log2`.
	Function of Float is math_log2(Float is v);

	## Base-10 logarithm. Bound to `spec_math_log10`.
	Function of Float is math_log10(Float is v);

	## Power base^exp. Bound to `spec_math_pow`.
	Function of Float is math_pow(Float is base, Float is exp);

	## Fused multiply-add (a * b + c) with single rounding. Bound to `spec_math_fma`.
	Function of Float is math_fma(Float is a, Float is b, Float is c);

	## Float-to-Int truncation toward zero. Bound to `spec_math_to_int`.
	Function of Int is math_to_int(Float is v);

	## Int-to-Float conversion. Bound to `spec_math_to_float`.
	Function of Float is math_to_float(Int is v);

	## Lock-free thread-local uniform float in [0, 1). Bound to `spec_fast_random`.
	Function of Float is fast_random();
}
