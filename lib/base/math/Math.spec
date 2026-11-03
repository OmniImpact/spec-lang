#! Package base:math
#! Provides mathematical constants, floating point operations, and algorithms.

## Mathematical functions and algorithmic primitives.
class Math{

	## Rounds a floating point number to the nearest whole integer.
	##
	## @param value: Input floating point number.
	## @return: Nearest whole number float.
	replace Function of Float is round(Float is value){
	}

	## Computes the largest integer less than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Floored float.
	replace Function of Float is floor(Float is value){
	}

	## Computes the smallest integer greater than or equal to [value].
	##
	## @param value: Input floating point number.
	## @return: Ceiled float.
	replace Function of Float is ceil(Float is value){
	}

	## Generates a pseudo-random floating point number in range `[min, max)`.
	##
	## @param min: Lower bound (inclusive).
	## @param max: Upper bound (exclusive).
	## @return: Random float within range.
	replace Function of Float is random(Float is min, Float is max){
	}

	## Returns the absolute (non-negative) magnitude of [value].
	##
	## @param value: Input number.
	## @return: Non-negative magnitude float.
	Function of Float is abs(Float is value){
		if (value < 0.0) {
			return -value;
		}
		return value;
	}

	## Computes the minimum of two values.
	##
	## @param a: First operand.
	## @param b: Second operand.
	## @return: Smaller of [a] and [b].
	Function of Float is min(Float is a, Float is b){
		if (a < b) {
			return a;
		}
		return b;
	}

	## Computes the maximum of two values.
	##
	## @param a: First operand.
	## @param b: Second operand.
	## @return: Larger of [a] and [b].
	Function of Float is max(Float is a, Float is b){
		if (a > b) {
			return a;
		}
		return b;
	}

	## Restricts [val] to lie within the closed range `[minVal, maxVal]`.
	##
	## @param val: Value to clamp.
	## @param minVal: Lower bound.
	## @param maxVal: Upper bound.
	## @return: Clamped value.
	Function of Float is clamp(Float is val, Float is minVal, Float is maxVal){
		if (val < minVal) {
			return minVal;
		}
		if (val > maxVal) {
			return maxVal;
		}
		return val;
	}

}
