#! Package specunit
#! The assertion surface: held functions recording soft failures into the
#! SpecUnit registry singleton. Held functions do not overload, so the
#! equality asserts are typed by name (areEqualInt / areEqualString) —
#! the invoke ladder's future Any-marshal rung is what unifies them.
#! See SPECUNIT.md.

Class is Assert{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', SpecUnit]
	];

	## Records a failure against the current test.
	##
	## @param message: The failure message.
	held Function is fail(String is message){
		SpecUnit:addFailure(msg: message);
	}

	## Integer equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualInt(Int is expected, Int is actual){
		Conditional:if(check: { expected != actual }, then: {
			SpecUnit:addFailure(msg: 'expected ' . (expected as String) . ', got ' . (actual as String) . ' (areEqualInt)');
		});
	}

	## Integer inequality: [notExpected] must differ from [actual].
	##
	## @param notExpected: The forbidden value.
	## @param actual: The actual value.
	held Function is areNotEqualInt(Int is notExpected, Int is actual){
		Conditional:if(check: { notExpected == actual }, then: {
			SpecUnit:addFailure(msg: 'expected anything but ' . (actual as String) . ' (areNotEqualInt)');
		});
	}

	## String equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualString(String is expected, String is actual){
		Conditional:if(check: { expected != actual }, then: {
			SpecUnit:addFailure(msg: 'expected \'' . expected . '\', got \'' . actual . '\' (areEqualString)');
		});
	}

	## Float closeness within [delta] — never raw == on doubles.
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	## @param delta: The inclusive tolerance.
	held Function is areClose(Float is expected, Float is actual, Float is delta){
		Conditional:if(check: { (expected - actual) > delta || (actual - expected) > delta }, then: {
			SpecUnit:addFailure(msg: 'expected ' . (expected as String) . ' +/- ' . (delta as String) . ', got ' . (actual as String) . ' (areClose)');
		});
	}

	## Boolean truth.
	##
	## @param condition: The condition that must hold.
	held Function is isTrue(Boolean is condition){
		Conditional:if(check: { !condition }, then: {
			SpecUnit:addFailure(msg: 'isTrue failed');
		});
	}

	## Boolean falsity.
	##
	## @param condition: The condition that must not hold.
	held Function is isFalse(Boolean is condition){
		Conditional:if(check: { condition }, then: {
			SpecUnit:addFailure(msg: 'isFalse failed');
		});
	}
}
