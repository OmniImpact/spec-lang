#! Package specunit
#! The assertion surface: held functions appending CheckRecords into the
#! SpecUnitState registry — UNCONDITIONALLY (the ok flag carries the
#! outcome; the runner interprets records in endTest). Held bodies cannot
#! branch, so the records are data by design. Held functions do not
#! overload, so the equality asserts are typed by name — the invoke
#! ladder's future Any-marshal rung is what unifies them. See SPECUNIT.md.

Class is Assert{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitState],
		['specunit', CheckRecord]
	];

	## Records an unconditional failure.
	##
	## @param message: The failure message.
	held Function is fail(String is message){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: false, msg: message));
	}

	## Integer equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualInt(Int is expected, Int is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: expected == actual, msg: 'expected ' . (expected as String) . ', got ' . (actual as String) . ' (areEqualInt)'));
	}

	## Integer inequality: [notExpected] must differ from [actual].
	##
	## @param notExpected: The forbidden value.
	## @param actual: The actual value.
	held Function is areNotEqualInt(Int is notExpected, Int is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: notExpected != actual, msg: 'expected anything but ' . (actual as String) . ' (areNotEqualInt)'));
	}

	## String equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualString(String is expected, String is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: expected == actual, msg: 'expected \'' . expected . '\', got \'' . actual . '\' (areEqualString)'));
	}

	## Float closeness within [delta] — never raw == on doubles.
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	## @param delta: The inclusive tolerance.
	held Function is areClose(Float is expected, Float is actual, Float is delta){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: !((expected - actual) > delta || (actual - expected) > delta), msg: 'expected ' . (expected as String) . ' +/- ' . (delta as String) . ', got ' . (actual as String) . ' (areClose)'));
	}

	## Boolean truth.
	##
	## @param condition: The condition that must hold.
	held Function is isTrue(Boolean is condition){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: condition, msg: 'isTrue failed'));
	}

	## Boolean falsity.
	##
	## @param condition: The condition that must not hold.
	held Function is isFalse(Boolean is condition){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: !condition, msg: 'isFalse failed'));
	}
}
