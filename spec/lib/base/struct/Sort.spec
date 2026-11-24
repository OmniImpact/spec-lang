#! Package base:struct
#! Sorting utilities for integer, string, and custom-comparator arrays.

## In-place and copying sorting utilities for arrays of integers, strings, and custom-compared items.
Class is Sort{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Sorts [values] in place in ascending integer order using quicksort.
	Function is sortInts(Array of Int is values){
		local Int is len: values:length();
		if({ len > 1 }, {
			:qsortInts(values: values, lo: 0, hi: len - 1, desc: false);
		});
	}

	## Sorts [values] in place in descending integer order using quicksort.
	Function is sortIntsDesc(Array of Int is values){
		local Int is len: values:length();
		if({ len > 1 }, {
			:qsortInts(values: values, lo: 0, hi: len - 1, desc: true);
		});
	}

	## Returns a new array containing [values] sorted in ascending integer order.
	Function of Array of Int is ints(Array of Int is values){
		local Array of Int is out: values:copy();
		:sortInts(values: out);
		return out;
	}

	## Returns a new array containing [values] sorted in descending integer order.
	Function of Array of Int is intsDesc(Array of Int is values){
		local Array of Int is out: values:copy();
		:sortIntsDesc(values: out);
		return out;
	}

	## Sorts [values] in place in ascending lexicographical order.
	Function is sortStrings(Array of String is values){
		local Int is len: values:length();
		if({ len > 1 }, {
			:qsortStrings(values: values, lo: 0, hi: len - 1, desc: false);
		});
	}

	## Sorts [values] in place in descending lexicographical order.
	Function is sortStringsDesc(Array of String is values){
		local Int is len: values:length();
		if({ len > 1 }, {
			:qsortStrings(values: values, lo: 0, hi: len - 1, desc: true);
		});
	}

	## Returns a new array containing [values] sorted in ascending lexicographical order.
	Function of Array of String is strings(Array of String is values){
		local Array of String is out: values:copy();
		:sortStrings(values: out);
		return out;
	}

	## Returns a new array containing [values] sorted in descending lexicographical order.
	Function of Array of String is stringsDesc(Array of String is values){
		local Array of String is out: values:copy();
		:sortStringsDesc(values: out);
		return out;
	}

	## Sorts [values] in place using [compare](a, b) returning `< 0` if `a < b`, `0` if equal, `> 0` if `a > b`.
	Function is sortBy(Array is values, Function of Int is compare){
		local Int is len: values:length();
		if({ len > 1 }, {
			:qsortBy(values: values, lo: 0, hi: len - 1, compare: compare);
		});
	}

	## Returns a new array containing [values] sorted using [compare](a, b).
	Function of Array is by(Array is values, Function of Int is compare){
		local Array is out: values:copy();
		:sortBy(values: out, compare: compare);
		return out;
	}

	local Function is qsortInts(Array of Int is values, Int is lo, Int is hi, Boolean is desc){
		if({ lo >= hi }, {
			return;
		});
		local Int is pivot: values:get(index: (lo + hi) / 2, default: 0);
		local Int is i: lo;
		local Int is j: hi;
		while({ i <= j }, {
			if({ desc }, {
				while({ values:get(index: i, default: 0) > pivot }, { i: i + 1; });
				while({ values:get(index: j, default: 0) < pivot }, { j: j - 1; });
			}, {
				while({ values:get(index: i, default: 0) < pivot }, { i: i + 1; });
				while({ values:get(index: j, default: 0) > pivot }, { j: j - 1; });
			});
			if({ i <= j }, {
				local Int is tmp: values:get(index: i, default: 0);
				values:set(index: i, item: values:get(index: j, default: 0));
				values:set(index: j, item: tmp);
				i: i + 1;
				j: j - 1;
			});
		});
		if({ lo < j }, { :qsortInts(values: values, lo: lo, hi: j, desc: desc); });
		if({ i < hi }, { :qsortInts(values: values, lo: i, hi: hi, desc: desc); });
	}

	local Function is qsortStrings(Array of String is values, Int is lo, Int is hi, Boolean is desc){
		if({ lo >= hi }, {
			return;
		});
		local String is pivot: values:get(index: (lo + hi) / 2, default: '');
		local Int is i: lo;
		local Int is j: hi;
		while({ i <= j }, {
			if({ desc }, {
				while({ values:get(index: i, default: '') > pivot }, { i: i + 1; });
				while({ values:get(index: j, default: '') < pivot }, { j: j - 1; });
			}, {
				while({ values:get(index: i, default: '') < pivot }, { i: i + 1; });
				while({ values:get(index: j, default: '') > pivot }, { j: j - 1; });
			});
			if({ i <= j }, {
				local String is tmp: values:get(index: i, default: '');
				values:set(index: i, item: values:get(index: j, default: ''));
				values:set(index: j, item: tmp);
				i: i + 1;
				j: j - 1;
			});
		});
		if({ lo < j }, { :qsortStrings(values: values, lo: lo, hi: j, desc: desc); });
		if({ i < hi }, { :qsortStrings(values: values, lo: i, hi: hi, desc: desc); });
	}

	local Function is qsortBy(Array is values, Int is lo, Int is hi, Function of Int is compare){
		if({ lo >= hi }, {
			return;
		});
		local Any is pivot: values:get(index: (lo + hi) / 2, default: '');
		local Int is i: lo;
		local Int is j: hi;
		while({ i <= j }, {
			local Boolean is scanI: true;
			while({ scanI }, {
				local Any is curI: values:get(index: i, default: '');
				if({ compare(curI, pivot) < 0 }, {
					i: i + 1;
				}, {
					scanI: false;
				});
			});
			local Boolean is scanJ: true;
			while({ scanJ }, {
				local Any is curJ: values:get(index: j, default: '');
				if({ compare(curJ, pivot) > 0 }, {
					j: j - 1;
				}, {
					scanJ: false;
				});
			});
			if({ i <= j }, {
				local Any is tmp: values:get(index: i, default: '');
				values:set(index: i, item: values:get(index: j, default: ''));
				values:set(index: j, item: tmp);
				i: i + 1;
				j: j - 1;
			});
		});
		if({ lo < j }, { :qsortBy(values: values, lo: lo, hi: j, compare: compare); });
		if({ i < hi }, { :qsortBy(values: values, lo: i, hi: hi, compare: compare); });
	}

}
