Class is ByteTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Byte Test ===');

		# Case 1: Int to Byte cast, small values pass through
		local Byte is b97: 97 as Byte;
		if (b97 as Int == 97) {
			output:line('[PASS] 97 as Byte round-trips');
		} else {
			output:line('[FAIL] 97 as Byte round-trip: ' . (b97 as Int) as String);
		}

		# Case 2: mid-range value
		local Byte is b128: 128 as Byte;
		if (b128 as Int == 128) {
			output:line('[PASS] 128 as Byte round-trips');
		} else {
			output:line('[FAIL] 128 as Byte: ' . (b128 as Int) as String);
		}

		# Case 3: boundaries
		local Byte is b0: 0 as Byte;
		local Byte is b255: 255 as Byte;
		if (b0 as Int == 0 && b255 as Int == 255) {
			output:line('[PASS] boundaries 0 and 255 preserved');
		} else {
			output:line('[FAIL] boundary round-trip');
		}

		# Case 4: Byte accepts any in-range Int expression
		local Int is computed: 64 * 2;
		local Byte is bexpr: computed as Byte;
		if (bexpr as Int == 128) {
			output:line('[PASS] computed Int cast to Byte');
		} else {
			output:line('[FAIL] computed cast: ' . (bexpr as Int) as String);
		}

		# Case 5: Byte survives storage in a field-like local and re-cast chains
		local Byte is stored: 72 as Byte;
		local Int is widened: stored as Int;
		local String is rendered: widened as String;
		if (rendered == '72') {
			output:line('[PASS] Byte -> Int -> String chain renders 72');
		} else {
			output:line('[FAIL] chain rendered: ' . rendered);
		}

		# Case 6: Byte to Byte cast is a no-op
		local Byte is same: stored as Byte;
		if (same as Int == 72) {
			output:line('[PASS] Byte as Byte is identity');
		} else {
			output:line('[FAIL] Byte as Byte altered value');
		}

		output:line('=== End Byte Test ===');
	}
}
