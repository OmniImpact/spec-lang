Class is ByteTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Byte Test ===');

		# Case 1: Int to Byte cast, small values pass through
		local Byte is b97: 97 as Byte;
		Conditional:if(check: { b97 as Int == 97 }, then: {
			Output:line('[PASS] 97 as Byte round-trips');
		}, else: {
			Output:line('[FAIL] 97 as Byte round-trip: ' . (b97 as Int) as String);
		});

		# Case 2: mid-range value
		local Byte is b128: 128 as Byte;
		Conditional:if(check: { b128 as Int == 128 }, then: {
			Output:line('[PASS] 128 as Byte round-trips');
		}, else: {
			Output:line('[FAIL] 128 as Byte: ' . (b128 as Int) as String);
		});

		# Case 3: boundaries
		local Byte is b0: 0 as Byte;
		local Byte is b255: 255 as Byte;
		Conditional:if(check: { b0 as Int == 0 && b255 as Int == 255 }, then: {
			Output:line('[PASS] boundaries 0 and 255 preserved');
		}, else: {
			Output:line('[FAIL] boundary round-trip');
		});

		# Case 4: Byte accepts any in-range Int expression
		local Int is computed: 64 * 2;
		local Byte is bexpr: computed as Byte;
		Conditional:if(check: { bexpr as Int == 128 }, then: {
			Output:line('[PASS] computed Int cast to Byte');
		}, else: {
			Output:line('[FAIL] computed cast: ' . (bexpr as Int) as String);
		});

		# Case 5: Byte survives storage in a field-like local and re-cast chains
		local Byte is stored: 72 as Byte;
		local Int is widened: stored as Int;
		local String is rendered: widened as String;
		Conditional:if(check: { rendered == '72' }, then: {
			Output:line('[PASS] Byte -> Int -> String chain renders 72');
		}, else: {
			Output:line('[FAIL] chain rendered: ' . rendered);
		});

		# Case 6: Byte to Byte cast is a no-op
		local Byte is same: stored as Byte;
		Conditional:if(check: { same as Int == 72 }, then: {
			Output:line('[PASS] Byte as Byte is identity');
		}, else: {
			Output:line('[FAIL] Byte as Byte altered value');
		});

		Output:line('=== End Byte Test ===');
	}
}
