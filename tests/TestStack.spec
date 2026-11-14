#! SpecUnit test suite for base:struct:Stack.

Class of SpecUnitTest is TestStack{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Stack],
		['base', 'struct', Array]
	];

	## Case 1: Empty stack query behaviors and fallbacks.
	Function is testEmptyStack(){
		local Stack of String is s: Stack:init();
		Assert:areEqualInt(0, s:length());
		Assert:isTrue(s:isEmpty());
		Assert:areEqualString('none', s:peek(default: 'none'));
		Assert:areEqualString('empty', s:pop(default: 'empty'));
	}

	## Case 2: Pushing elements and peeking top element without removing.
	Function is testPushAndPeek(){
		local Stack of String is s: Stack:init();
		s:push(item: 'first');
		Assert:areEqualInt(1, s:length());
		Assert:isFalse(s:isEmpty());
		Assert:areEqualString('first', s:peek(default: ''));

		s:push(item: 'second');
		Assert:areEqualInt(2, s:length());
		Assert:areEqualString('second', s:peek(default: ''));

		s:push(item: 'third');
		Assert:areEqualInt(3, s:length());
		Assert:areEqualString('third', s:peek(default: ''));
	}

	## Case 3: LIFO order verification via successive pops.
	Function is testLIFOOrder(){
		local Stack of String is s: Stack:init();
		s:push(item: 'alpha');
		s:push(item: 'beta');
		s:push(item: 'gamma');

		Assert:areEqualString('gamma', s:pop(default: ''));
		Assert:areEqualInt(2, s:length());

		Assert:areEqualString('beta', s:pop(default: ''));
		Assert:areEqualInt(1, s:length());

		Assert:areEqualString('alpha', s:pop(default: ''));
		Assert:areEqualInt(0, s:length());
		Assert:isTrue(s:isEmpty());

		# Underflow yields default
		Assert:areEqualString('fallback', s:pop(default: 'fallback'));
	}

	## Case 4: Clear empties the stack.
	Function is testClear(){
		local Stack of String is s: Stack:init();
		s:push(item: 'x');
		s:push(item: 'y');
		s:push(item: 'z');
		Assert:areEqualInt(3, s:length());

		s:clear();
		Assert:areEqualInt(0, s:length());
		Assert:isTrue(s:isEmpty());
		Assert:areEqualString('empty', s:pop(default: 'empty'));
	}

	## Case 5: toArray snapshot returns elements from bottom to top.
	Function is testToArray(){
		local Stack of String is s: Stack:init();
		s:push(item: 'bottom');
		s:push(item: 'middle');
		s:push(item: 'top');

		local Array of String is arr: s:toArray();
		Assert:areEqualInt(3, arr:length());
		Assert:areEqualString('bottom', arr:get(index: 0, default: ''));
		Assert:areEqualString('middle', arr:get(index: 1, default: ''));
		Assert:areEqualString('top', arr:get(index: 2, default: ''));

		# Mutating the stack does not change the snapshot array
		s:pop(default: '');
		Assert:areEqualInt(2, s:length());
		Assert:areEqualInt(3, arr:length());
	}
}
