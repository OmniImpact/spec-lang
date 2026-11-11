#! Package base:math
#! Mathematical constants, floating point operations, and algorithms.

## Mathematical functions and algorithmic primitives.
##
## Runtime-managed: the libm-backed functions bind
## to `external` libm declarations at the floor; the pure functions ([abs],
## [min], [max], [clamp]) are real Spec bodies.

Class is Math{
	namespace: ['base', 'math'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
];

	## Rounds a floating point number to the nearest whole integer.
	##
	## @param value: Input floating point number.
	## @return: Nearest whole number float.
	Function of Float is round(Float is value){
	}

	## Computes the largest integer less than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Floored float.
	Function of Float is floor(Float is value){
	}

	## Computes the smallest integer greater than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Ceiled float.
	Function of Float is ceil(Float is value){
	}

	## Converts a floating point number to an Int by truncation toward zero.
	##
	## @param value: Input floating point number.
	## @return: Truncated integer value.
	Function of Int is toInt(Float is value){
	}

	## Converts a 64-bit integer to a double-precision floating point number.
	##
	## @param value: Input integer value.
	## @return: Floating point representation.
	Function of Float is toFloat(Int is value){
	}

	## Computes the non-negative square root of [value].
	##
	## @param value: Input non-negative floating point number.
	## @return: Square root of [value], or `0.0` if negative.
	Function of Float is sqrt(Float is value){
	}

	## Computes the trigonometric sine of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Sine of [value].
	Function of Float is sin(Float is value){
	}

	## Computes the trigonometric cosine of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Cosine of [value].
	Function of Float is cos(Float is value){
	}

	## Computes the trigonometric tangent of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Tangent of [value].
	Function of Float is tan(Float is value){
	}

	## Computes the principal value of the arc tangent of `y / x` in radians.
	##
	## @param y: Vertical coordinate.
	## @param x: Horizontal coordinate.
	## @return: Angle in radians in [-pi, pi].
	Function of Float is atan2(Float is y, Float is x){
	}

	## Computes the natural logarithm (base e) of [value].
	##
	## @param value: Positive input number.
	## @return: Natural logarithm of [value], or `0.0` if non-positive.
	Function of Float is log(Float is value){
	}

	## Computes the base-2 logarithm of [value].
	##
	## @param value: Positive input number.
	## @return: Base-2 logarithm of [value], or `0.0` if non-positive.
	Function of Float is log2(Float is value){
	}

	## Computes [base] raised to the power [exp].
	##
	## @param base: Base floating point number.
	## @param exp: Exponent floating point number.
	## @return: Result of base^exp.
	Function of Float is pow(Float is base, Float is exp){
	}

	## Generates a pseudo-random floating point number in range [min, max).
	##
	## @param min: Lower bound (inclusive).
	## @param max: Upper bound (exclusive).
	## @return: Random float within range.
	Function of Float is random(Float is min, Float is max){
	}

	## Generates a lock-free per-thread uniform float in [0, 1).
	##
	## Backed by a thread-local xorshift64* generator; safe and scalable from
	## parallel worker threads (each thread gets a distinct deterministic seed).
	##
	## @return: Uniform float in [0, 1).
	Function of Float is fastRandom(){
	}

	## Returns the absolute (non-negative) magnitude of [value].
	##
	## @param value: Input number.
	## @return: Non-negative magnitude float.
	Function of Float is abs(Float is value){
		if({ value < 0.0 }, {
			return -value;
		});
		return value;
	}

	## Integer absolute value (§I: type-distinct overload).
	##
	## @param value: Input integer.
	## @return: Non-negative magnitude.
	Function of Int is abs(Int is value){
		if({ value < 0 }, {
			return -value;
		});
		return value;
	}

	## Computes the minimum of two values.
	##
	## @param a: First operand.
	## @param b: Second operand.
	## @return: Smaller of [a] and [b].
	Function of Float is min(Float is a, Float is b){
		if({ a < b }, {
			return a;
		});
		return b;
	}

	## Computes the maximum of two values.
	##
	## @param a: First operand.
	## @param b: Second operand.
	## @return: Larger of [a] and [b].
	Function of Float is max(Float is a, Float is b){
		if({ a > b }, {
			return a;
		});
		return b;
	}

	## Restricts [val] to lie within the closed range [minVal, maxVal].
	##
	## @param val: Value to clamp.
	## @param minVal: Lower bound.
	## @param maxVal: Upper bound.
	## @return: Clamped value.
	Function of Float is clamp(Float is val, Float is minVal, Float is maxVal){
		return match(when: [
			{ val < minVal }: { minVal },
			{ val > maxVal }: { maxVal },
			else:             { val }
		]);
	}
}
