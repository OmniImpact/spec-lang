#! SpecUnit sweep (from list_byte_test.spec): the [Byte] buffer —
#! push/appendString/length accounting, get with defaults and error
#! callbacks, set overwrite and OOB notification, pop semantics,
#! toString freezing, ARC aliasing, and clear-then-reuse.

Class of SpecUnitTest is TestListByte{

	replace [[String]] is using: [
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

	## Case 2: get and [] read back bytes in bounds.
	Function is testGetReadsBack(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		local Int is first: buf:get(index: 0) as Int;
		local Int is second: buf[1] as Int;
		Assert:areEqualInt(72, first);
		Assert:areEqualInt(105, second);
	}

	## Case 3: set overwrites in place.
	Function is testSetOverwrite(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		buf:set(index: 0, item: 74 as Byte);
		local Int is rewritten: buf:get(index: 0) as Int;
		Assert:areEqualInt(74, rewritten);
	}

	## Case 4: pop returns the last byte and shrinks length.
	Function is testPopLast(){
		local [Byte] is buf;
		buf:push(item: 72 as Byte);
		buf:push(item: 105 as Byte);
		buf:appendString(value: '!');
		local Byte is last: buf:pop();
		Assert:areEqualInt(33, last as Int);
		Assert:areEqualInt(2, buf:length());
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
