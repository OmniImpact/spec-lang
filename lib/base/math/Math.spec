class Math{

	replace Function of Float is round(Float is value){
	}

	replace Function of Float is floor(Float is value){
	}

	replace Function of Float is ceil(Float is value){
	}

	replace Function of Float is random(Float is min, Float is max){
	}

	Function of Float is abs(Float is value){
		if (value < 0.0) {
			return -value;
		}
		return value;
	}

	Function of Float is min(Float is a, Float is b){
		if (a < b) {
			return a;
		}
		return b;
	}

	Function of Float is max(Float is a, Float is b){
		if (a > b) {
			return a;
		}
		return b;
	}

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
