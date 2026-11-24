#! Package base:math
#! Statistical and aggregate functions over arrays of numbers.

## Aggregate and statistical operations over numeric arrays (`min`, `max`, `sum`, `average`, `median`, `variance`, `stdDev`).
Class is Stats{
	replace [String] is namespace: ['base', 'math'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'math', as Math()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Returns the sum of all integers in [values] (`0` when empty).
	Function of Int is sum(Array of Int is values){
		local Int is total: 0;
		local Int is len: values:length();
		local Int is i: 0;
		while({ i < len }, {
			total: total + values:get(index: i, default: 0);
			i: i + 1;
		});
		return total;
	}

	## Returns the arithmetic mean of [values] (`0.0` when empty).
	Function of Float is average(Array of Int is values){
		local Int is len: values:length();
		if({ len == 0 }, {
			return 0.0;
		});
		return toFloat(value: :sum(values: values)) / toFloat(value: len);
	}

	## Returns the smallest integer in [values], or [default] when empty.
	Function of Int is min(Array of Int is values, Int is default: 0){
		local Int is len: values:length();
		if({ len == 0 }, {
			return default;
		});
		local Int is best: values:get(index: 0, default: default);
		local Int is i: 1;
		while({ i < len }, {
			local Int is cur: values:get(index: i, default: best);
			if({ cur < best }, {
				best: cur;
			});
			i: i + 1;
		});
		return best;
	}

	## Returns the largest integer in [values], or [default] when empty.
	Function of Int is max(Array of Int is values, Int is default: 0){
		local Int is len: values:length();
		if({ len == 0 }, {
			return default;
		});
		local Int is best: values:get(index: 0, default: default);
		local Int is i: 1;
		while({ i < len }, {
			local Int is cur: values:get(index: i, default: best);
			if({ cur > best }, {
				best: cur;
			});
			i: i + 1;
		});
		return best;
	}

	## Returns the median of [values] (`0.0` when empty).
	Function of Float is median(Array of Int is values){
		local Int is len: values:length();
		if({ len == 0 }, {
			return 0.0;
		});
		local Array of Int is sorted: values:copy();
		local Int is i: 1;
		while({ i < len }, {
			local Int is key: sorted:get(index: i, default: 0);
			local Int is j: i - 1;
			while({ j >= 0 && sorted:get(index: j, default: 0) > key }, {
				sorted:set(index: j + 1, item: sorted:get(index: j, default: 0));
				j: j - 1;
			});
			sorted:set(index: j + 1, item: key);
			i: i + 1;
		});
		local Int is mid: len / 2;
		if({ (len % 2) == 1 }, {
			return toFloat(value: sorted:get(index: mid, default: 0));
		});
		local Int is lo: sorted:get(index: mid - 1, default: 0);
		local Int is hi: sorted:get(index: mid, default: 0);
		return toFloat(value: lo + hi) / 2.0;
	}

	## Returns the population variance of [values] (`0.0` when empty).
	Function of Float is variance(Array of Int is values){
		local Int is len: values:length();
		if({ len == 0 }, {
			return 0.0;
		});
		local Float is mean: :average(values: values);
		local Float is acc: 0.0;
		local Int is i: 0;
		while({ i < len }, {
			local Float is diff: toFloat(value: values:get(index: i, default: 0)) - mean;
			acc: acc + (diff * diff);
			i: i + 1;
		});
		return acc / toFloat(value: len);
	}

	## Returns the population standard deviation of [values] (`0.0` when empty).
	Function of Float is stdDev(Array of Int is values){
		return sqrt(value: :variance(values: values));
	}

}
