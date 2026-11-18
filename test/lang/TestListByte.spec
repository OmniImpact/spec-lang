#! SpecUnit sweep (from list_byte_test.spec): the [Byte] buffer —
#! push/appendString/length accounting, get with defaults and error
#! callbacks, set overwrite and OOB notification, pop semantics,
#! toString freezing, ARC aliasing, and clear-then-reuse.

Class of SpecUnitTest is TestListByte{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', List]
	];

	## Case 1: push/appendString/length.
	Function is testPushAppendStringLength(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		Assert:areEqualInt(3, buf:length());
	}

	## Case 2: get reads back; the error callback stays untouched on success.
	Function is testGetReadsBackWithoutError(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		local [Byte] is errFlag;
		local Int is first: buf:get(index: 0, default: 0 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		}) as Int;
		Assert:areEqualInt(72, first);
		Assert:areEqualInt(0, errFlag:length());
	}

	## Case 3: OOB get yields the default AND notifies the error callback.
	Function is testOobGetDefaultAndNotify(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		local [Byte] is errFlag;
		local Byte is oob: buf:get(index: 9, default: 7 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Assert:areEqualInt(7, oob as Int);
		Assert:areEqualInt(1, errFlag:length());
	}

	## Case 4: omitted error callback is legal (no-op default).
	Function is testOmittedErrorCallback(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		local Byte is silent: buf:get(index: 42, default: 3 as Byte);
		Assert:areEqualInt(3, silent as Int);
	}

	## Case 5: set overwrites in place; OOB set notifies the provided callback.
	Function is testSetOverwriteAndOobNotify(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		local [Byte] is errFlag;
		buf:set(index: 0, item: 74 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		local Int is rewritten: buf:get(index: 0, default: 0 as Byte) as Int;
		buf:set(index: 99, item: 1 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Assert:areEqualInt(74, rewritten);
		Assert:areEqualInt(1, errFlag:length());
	}

	## Case 6: pop returns the last byte; pop on empty yields the default
	## and notifies the error callback.
	Function is testPopLastAndEmptyNotify(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		local Byte is last: buf:pop(default: 0 as Byte);
		local [Byte] is empty;
		local [Byte] is errFlag;
		local Byte is nothing: empty:pop(default: 9 as Byte, error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		Assert:areEqualInt(33, last as Int);
		Assert:areEqualInt(9, nothing as Int);
		Assert:areEqualInt(1, errFlag:length());
	}

	## Case 7: toString freezes the buffer contents.
	Function is testToStringFreezes(){
		local [Byte] is builder;
		builder:appendString(value: 'Hi');
		builder:push(item: 33 as Byte);
		local String is frozen: builder:toString();
		Assert:areEqualString('Hi!', frozen);
	}

	## Case 8: assignment shares the ARC-managed buffer.
	Function is testAssignmentAliases(){
		local [Byte] is builder;
		builder:appendString(value: 'Hi');
		builder:push(item: 33 as Byte);
		local [Byte] is alias: builder;
		alias:appendString(value: '!');
		Assert:areEqualInt(4, builder:length());
	}

	## Case 9: clear empties but the buffer stays usable.
	Function is testClearStaysUsable(){
		local [Byte] is builder;
		builder:appendString(value: 'Hi');
		builder:push(item: 33 as Byte);
		local [Byte] is alias: builder;
		alias:appendString(value: '!');
		builder:clear();
		Assert:areEqualInt(0, builder:length());
		builder:push(item: 65 as Byte);
		Assert:areEqualInt(1, builder:length());
	}
}
