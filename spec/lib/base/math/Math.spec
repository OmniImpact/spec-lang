#! Package base:math
#! Mathematical constants, floating point operations, and algorithms.

## Mathematical functions and algorithmic primitives.
##
## Hardware-accelerated and libm primitives delegate to `base:sysinternal:Math`;
## rounding, constants, clamping, hyperbolic functions, and array reductions
## are implemented in pure Spec.

Class is Math{
	namespace: ['base', 'math'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Math],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Rounds a floating point number to the nearest whole integer (half away from zero).
	##
	## @param value: Input floating point number.
	## @return: Nearest whole number float.
	Function of Float is round(Float is value){
		if({ !(value == value) || value >= 4503599627370496.0 || value <= -4503599627370496.0 }, {
			return value;
		});
		if({ value >= 0.0 }, {
			local Float is fl: self:floor(value: value);
			if({ (value - fl) >= 0.5 }, {
				return fl + 1.0;
			});
			return fl;
		});
		local Float is ce: self:ceil(value: value);
		if({ (ce - value) >= 0.5 }, {
			return ce - 1.0;
		});
		return ce;
	}

	## Computes the largest integer less than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Floored float.
	Function of Float is floor(Float is value){
		if({ !(value == value) || value >= 4503599627370496.0 || value <= -4503599627370496.0 }, {
			return value;
		});
		local Int is i: self:toInt(value: value);
		local Float is f: self:toFloat(value: i);
		if({ f > value }, {
			return f - 1.0;
		});
		return f;
	}

	## Computes the smallest integer greater than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Ceiled float.
	Function of Float is ceil(Float is value){
		if({ !(value == value) || value >= 4503599627370496.0 || value <= -4503599627370496.0 }, {
			return value;
		});
		local Int is i: self:toInt(value: value);
		local Float is f: self:toFloat(value: i);
		if({ f < value }, {
			return f + 1.0;
		});
		return f;
	}

	## Converts a floating point number to an Int by truncation toward zero.
	##
	## @param value: Input floating point number.
	## @return: Truncated integer value.
	Function of Int is toInt(Float is value){
		return base:sysinternal:Math:math_to_int(v: value);
	}

	## Converts a 64-bit integer to a double-precision floating point number.
	##
	## @param value: Input integer value.
	## @return: Floating point representation.
	Function of Float is toFloat(Int is value){
		return base:sysinternal:Math:math_to_float(v: value);
	}

	## Computes the non-negative square root of [value].
	##
	## @param value: Input non-negative floating point number.
	## @return: Square root of [value], or `0.0` if negative.
	Function of Float is sqrt(Float is value){
		return base:sysinternal:Math:math_sqrt(v: value);
	}

	## Computes the cube root of [value].
	##
	## @param value: Input floating point number.
	## @return: Cube root of [value].
	Function of Float is cbrt(Float is value){
		return base:sysinternal:Math:math_cbrt(v: value);
	}

	## Computes the trigonometric sine of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Sine of [value].
	Function of Float is sin(Float is value){
		return base:sysinternal:Math:math_sin(v: value);
	}

	## Computes the trigonometric cosine of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Cosine of [value].
	Function of Float is cos(Float is value){
		return base:sysinternal:Math:math_cos(v: value);
	}

	## Computes the trigonometric tangent of [value] (in radians).
	##
	## @param value: Angle in radians.
	## @return: Tangent of [value].
	Function of Float is tan(Float is value){
		return base:sysinternal:Math:math_tan(v: value);
	}

	## Computes the arc sine of [value] (in radians).
	##
	## @param value: Input in [-1.0, 1.0].
	## @return: Angle in radians in [-pi/2, pi/2].
	Function of Float is asin(Float is value){
		return base:sysinternal:Math:math_asin(v: value);
	}

	## Computes the arc cosine of [value] (in radians).
	##
	## @param value: Input in [-1.0, 1.0].
	## @return: Angle in radians in [0, pi].
	Function of Float is acos(Float is value){
		return base:sysinternal:Math:math_acos(v: value);
	}

	## Computes the arc tangent of [value] (in radians).
	##
	## @param value: Input value.
	## @return: Angle in radians in [-pi/2, pi/2].
	Function of Float is atan(Float is value){
		return base:sysinternal:Math:math_atan(v: value);
	}

	## Computes the principal value of the arc tangent of `y / x` in radians.
	##
	## @param y: Vertical coordinate.
	## @param x: Horizontal coordinate.
	## @return: Angle in radians in [-pi, pi].
	Function of Float is atan2(Float is y, Float is x){
		return base:sysinternal:Math:math_atan2(y: y, x: x);
	}

	## Computes `e` raised to the power [value].
	##
	## @param value: Exponent.
	## @return: `e^value`.
	Function of Float is exp(Float is value){
		return base:sysinternal:Math:math_exp(v: value);
	}

	## Computes the hyperbolic sine of [value].
	Function of Float is sinh(Float is value){
		return 0.5 * (self:exp(value: value) - self:exp(value: -value));
	}

	## Computes the hyperbolic cosine of [value].
	Function of Float is cosh(Float is value){
		return 0.5 * (self:exp(value: value) + self:exp(value: -value));
	}

	## Computes the hyperbolic tangent of [value].
	Function of Float is tanh(Float is value){
		if({ value > 20.0 }, {
			return 1.0;
		});
		if({ value < -20.0 }, {
			return -1.0;
		});
		local Float is e2x: self:exp(value: 2.0 * value);
		return (e2x - 1.0) / (e2x + 1.0);
	}

	## Computes the natural logarithm (base e) of [value].
	##
	## @param value: Positive input number.
	## @return: Natural logarithm of [value], or `0.0` if non-positive.
	Function of Float is log(Float is value){
		return base:sysinternal:Math:math_log(v: value);
	}

	## Computes the base-2 logarithm of [value].
	##
	## @param value: Positive input number.
	## @return: Base-2 logarithm of [value], or `0.0` if non-positive.
	Function of Float is log2(Float is value){
		return base:sysinternal:Math:math_log2(v: value);
	}

	## Computes the base-10 logarithm of [value].
	##
	## @param value: Positive input number.
	## @return: Base-10 logarithm of [value], or `0.0` if non-positive.
	Function of Float is log10(Float is value){
		return base:sysinternal:Math:math_log10(v: value);
	}

	## Computes [base] raised to the power [exp].
	##
	## @param base: Base floating point number.
	## @param exp: Exponent floating point number.
	## @return: Result of base^exp.
	Function of Float is pow(Float is base, Float is exp){
		return base:sysinternal:Math:math_pow(base: base, exp: exp);
	}

	## Computes `(a * b) + c` with a single rounding (hardware FMA when available).
	##
	## @param a: First multiplicand.
	## @param b: Second multiplicand.
	## @param c: Addend.
	## @return: Fused multiply-add result.
	Function of Float is fma(Float is a, Float is b, Float is c){
		return base:sysinternal:Math:math_fma(a: a, b: b, c: c);
	}

	## Generates a pseudo-random floating point number in range [min, max).
	##
	## @param min: Lower bound (inclusive).
	## @param max: Upper bound (exclusive).
	## @return: Random float within range.
	Function of Float is random(Float is min, Float is max){
		return min + ((max - min) * self:fastRandom());
	}

	## Generates a lock-free per-thread uniform float in [0, 1).
	##
	## Backed by a thread-local xorshift64* generator; safe and scalable from
	## parallel worker threads (each thread gets a distinct deterministic seed).
	##
	## @return: Uniform float in [0, 1).
	Function of Float is fastRandom(){
		local Int is x: tlsGetI64(slot: 0);
		if({ x == 0 }, {
			local Int is p: alloc(bytes: 8);
			free(ptr: p);
			x: p ^ -7046029254386353131;
			if({ x == 0 }, { x: 1; });
		});
		x: x ^ ((x >> 12) & 4503599627370495);
		x: x ^ (x << 25);
		x: x ^ ((x >> 27) & 137438953471);
		tlsSetI64(slot: 0, val: x);
		local Int is mant: ((x * 2685821657736338717) >> 11) & 9007199254740991;
		return self:toFloat(value: mant) * (1.0 / 9007199254740992.0);
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

	## Returns the smallest element in [values], or `0` if empty.
	Function of Int is min(Array of Int is values){
		if({ values:length() == 0 }, {
			return 0;
		});
		local Int is best: values:get(index: 0);
		local Int is idx: 1;
		while({ idx < values:length() }, {
			local Int is v: values:get(index: idx);
			if({ v < best }, {
				best: v;
			});
			idx: idx + 1;
		});
		return best;
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

	## Returns the largest element in [values], or `0` if empty.
	Function of Int is max(Array of Int is values){
		if({ values:length() == 0 }, {
			return 0;
		});
		local Int is best: values:get(index: 0);
		local Int is idx: 1;
		while({ idx < values:length() }, {
			local Int is v: values:get(index: idx);
			if({ v > best }, {
				best: v;
			});
			idx: idx + 1;
		});
		return best;
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

	## Returns the mathematical constant pi (3.141592653589793).
	Function of Float is pi(){
		return 3.141592653589793;
	}

	## Returns the circle constant tau = 2 * pi (6.283185307179586).
	Function of Float is tau(){
		return 6.283185307179586;
	}

	## Returns Euler's number e (2.718281828459045).
	Function of Float is e(){
		return 2.718281828459045;
	}

	## Returns the sign of [value]: `-1.0`, `0.0`, or `1.0`.
	Function of Float is sign(Float is value){
		return match(when: [
			{ value < 0.0 }: { -1.0 },
			{ value > 0.0 }: { 1.0 },
			else:            { 0.0 }
		]);
	}

	## Returns the sign of integer [value]: `-1`, `0`, or `1`.
	Function of Int is sign(Int is value){
		return match(when: [
			{ value < 0 }: { -1 },
			{ value > 0 }: { 1 },
			else:          { 0 }
		]);
	}

	## Linearly interpolates between [a] and [b] by [t] (`a + (b - a) * t`).
	Function of Float is lerp(Float is a, Float is b, Float is t){
		return a + ((b - a) * t);
	}

	## Converts degrees to radians.
	Function of Float is degToRad(Float is deg){
		return deg * 0.017453292519943295;
	}

	## Converts radians to degrees.
	Function of Float is radToDeg(Float is rad){
		return rad * 57.29577951308232;
	}

	## Computes the Euclidean hypotenuse `sqrt(x*x + y*y)`.
	Function of Float is hypot(Float is x, Float is y){
		return self:sqrt(value: (x * x) + (y * y));
	}
}
