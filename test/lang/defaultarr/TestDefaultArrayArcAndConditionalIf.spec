#! specunit: suite

Class of SpecUnitTest is TestDefaultArrayArcAndConditionalIf{
	replace [String] is namespace: ['test', 'lang', 'defaultarr'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', Conditional],
		['base', 'struct', Array],
		['test', 'lang', 'defaultarr', [DefArrItem, DefArrHolder]]
	];

	local Function of DefArrHolder is buildHolder(){
		local DefArrHolder is h: DefArrHolder();
		h:items:add(item: DefArrItem(label: 'alpha'));
		h:items:add(item: DefArrItem(label: 'beta'));
		return h;
	}

	held Function of String is pickString(Boolean is flag, String is a, String is b){
		return Conditional:if(check: { flag }, then: { a }, else: { b });
	}

	Function is testDefaultArrayParamRetainsArcElements(){
		local DefArrHolder is h: :buildHolder();
		Assert:areEqualInt(2, h:items:length());
		Assert:areEqualString('alpha', h:items:get(index: 0):label);
		Assert:areEqualString('beta', h:items:get(index: 1):label);
	}

	Function is testConditionalIfValueReturnInHeldMethod(){
		Assert:areEqualString('yes', TestDefaultArrayArcAndConditionalIf:pickString(flag: true, a: 'yes', b: 'no'));
		Assert:areEqualString('no', TestDefaultArrayArcAndConditionalIf:pickString(flag: false, a: 'yes', b: 'no'));
	}
}
