Class is ListByteTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', List],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== [Byte] Buffer Test ===');

		# Case 1: push/appendString/length
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		Conditional:if(check: { buf:length() == 3 }, then: {
			Output:line('[PASS] length after push/appendString is 3');
		}, else: {
			Output:line('[FAIL] length: ' . buf:length() as String);
		});

		# Case 2: get reads back, error callback untouched on success
		local [Byte] is errFlag;
		local Int is first: buf:get(index: 0, default: 0 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		}) as Int;
		Conditional:if(check: { first == 72 && errFlag:length() == 0 }, then: {
			Output:line('[PASS] get returns element; error callback not fired on success');
		}, else: {
			Output:line('[FAIL] get: first=' . first as String . ' errCount=' . errFlag:length() as String);
		});

		# Case 3: out-of-bounds get returns default AND fires error callback
		local Byte is oob: buf:get(index: 9, default: 7 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Conditional:if(check: { oob as Int == 7 && errFlag:length() == 1 }, then: {
			Output:line('[PASS] OOB get yields default and notifies error callback');
		}, else: {
			Output:line('[FAIL] OOB get: default=' . (oob as Int) as String . ' errCount=' . errFlag:length() as String);
		});

		# Case 4: omitted error callback is legal (no-op default)
		local Byte is silent: buf:get(index: 42, default: 3 as Byte);
		Conditional:if(check: { silent as Int == 3 }, then: {
			Output:line('[PASS] omitted error callback falls back to no-op');
		}, else: {
			Output:line('[FAIL] omitted error callback: ' . (silent as Int) as String);
		});

		# Case 5: set overwrites in place; OOB set notifies the provided callback
		buf:set(index: 0, item: 74 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		local Int is rewritten: buf:get(index: 0, default: 0 as Byte) as Int;
		buf:set(index: 99, item: 1 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Conditional:if(check: { rewritten == 74 && errFlag:length() == 2 }, then: {
			Output:line('[PASS] set writes in place; OOB set notifies');
		}, else: {
			Output:line('[FAIL] set: rewritten=' . rewritten as String . ' errCount=' . errFlag:length() as String);
		});

		# Case 6: pop returns last byte; pop on empty yields default + notification
		local Byte is last: buf:pop(default: 0 as Byte);
		local [Byte] is empty;
		local Byte is nothing: empty:pop(default: 9 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Conditional:if(check: { last as Int == 33 && nothing as Int == 9 && errFlag:length() == 3 }, then: {
			Output:line('[PASS] pop returns last byte; empty pop yields default and notifies');
		}, else: {
			Output:line('[FAIL] pop: last=' . (last as Int) as String . ' nothing=' . (nothing as Int) as String . ' errCount=' . errFlag:length() as String);
		});

		# Case 7: toString freezes the buffer
		local [Byte] is builder;
		builder:appendString(value: 'Hi');
		builder:push(item: 33 as Byte);
		local String is frozen: builder:toString();
		Conditional:if(check: { frozen == 'Hi!' }, then: {
			Output:line('[PASS] toString freezes buffer contents');
		}, else: {
			Output:line('[FAIL] toString: ' . frozen);
		});

		# Case 8: assignment shares the ARC-managed buffer
		local [Byte] is alias: builder;
		alias:appendString(value: '!');
		Conditional:if(check: { builder:length() == 4 }, then: {
			Output:line('[PASS] assignment aliases the same buffer');
		}, else: {
			Output:line('[FAIL] alias length: ' . builder:length() as String);
		});

		# Case 9: clear empties but stays usable
		builder:clear();
		Conditional:if(check: { builder:length() == 0 }, then: {
			builder:push(item: 65 as Byte);
			Conditional:if(check: { builder:length() == 1 }, then: {
				Output:line('[PASS] clear empties and buffer stays usable');
			}, else: {
				Output:line('[FAIL] push after clear');
			});
		}, else: {
			Output:line('[FAIL] clear: length=' . builder:length() as String);
		});

		Output:line('=== End [Byte] Buffer Test ===');
	}
}
