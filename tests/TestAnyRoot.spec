#! SpecUnit sweep (from any_root_test.spec): the root class `Any` —
#! implicit inheritance, default rendering, the typeName builtin, and
#! the root upcast/downcast round trip.
#! The test class is declared FIRST: the root file's first class is the
#! entry class, and the suite entry must be the test class so the
#! inherited argv-Map init runs the runner.

Class of SpecUnitTest is TestAnyRoot{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testDefaultToString(){
		local RootProbe is probe: RootProbe:init(id: 5);
		local String is label: 'probe: ' . probe;
		Assert:areEqualString('probe: RootProbe', label);
	}

	Function is testTypeNameBuiltin(){
		local RootProbe is probe: RootProbe:init(id: 5);
		Assert:areEqualString('RootProbe', probe:typeName());
	}

	Function is testTypeNameViaAny(){
		local RootProbe is probe: RootProbe:init(id: 5);
		local Any is asAny: probe;
		Assert:areEqualString('RootProbe', asAny:typeName());
	}

	Function is testToStringViaAny(){
		local RootProbe is probe: RootProbe:init(id: 5);
		local Any is asAny: probe;
		local String is strAny: asAny as String;
		Assert:areEqualString('RootProbe', strAny);
	}

	Function is testRoundTrip(){
		local RootProbe is probe: RootProbe:init(id: 5);
		local Any is up: probe as Any;
		local RootProbe is down: up as RootProbe;
		Assert:areEqualInt(5, down:id);
	}
}

Class is RootProbe{
	local Int is id: 5;

	replace Function is init(Int is id){
		self:id: id;
	}
}
