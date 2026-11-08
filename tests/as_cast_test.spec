#! Package examples:regression
#! Tracks the `as` cast operator across classes, numerics, and base pseudo-types.

## Type casts via `as`.
##
## Guarded behavior:
## - Class upcasts and downcasts through related hierarchies.
## - Numeric casts: Float -> Int truncation, Int -> Float widening.
## - Base pseudo-types format and parse: `as Hex/Bin/Oct` on Int yields a
##   String (with optional width), on String yields an Int.
## - Generated toString: concatenating a class instance renders its class
##   name; enum variants render their variant name.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Enum is Color {
	RED,
	GREEN
}

Class is Animal{

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];
	Function of String is speak(){
		return '...';
	}
}

Class of Animal is Dog{

	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];
	replace Function of String is speak(){
		return 'woof';
	}

	Function of String is fetch(){
		return 'ball';
	}
}

Class is AsCastTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: As Casts ===');

		# Case 1: upcast - dog passed and stored as Animal, dispatch stays virtual.
		local Dog is dog: Dog:init();
		local Animal is asAnimal: dog as Animal;
		if (asAnimal:speak() == 'woof') {
			Output:line('[PASS] upcast: virtual dispatch preserved');
		} else {
			Output:line('[FAIL] upcast: expected woof');
		}

		# Case 2: downcast - Animal reference back to Dog, subclass method reachable.
		local Dog is back: asAnimal as Dog;
		if (back:fetch() == 'ball') {
			Output:line('[PASS] downcast: subclass method reachable');
		} else {
			Output:line('[FAIL] downcast: expected ball');
		}

		# Case 3: numeric casts.
		local Int is truncated: 3.9 as Int;
		local Float is widened: 7 as Float;
		if (truncated == 3 && widened == 7.0) {
			Output:line('[PASS] numeric: 3.9 as Int = 3, 7 as Float = 7.0');
		} else {
			Output:line('[FAIL] numeric: ' . truncated . ', ' . widened);
		}

		# Case 4: base format and parse via pseudo-types.
		local String is hex: 65516 as Hex;
		local Int is parsed: 'ffec' as Hex;
		local String is bits: 10 as Bin(8);
		if (hex == 'ffec' && parsed == 65516 && bits == '00001010') {
			Output:line('[PASS] bases: as Hex, as Hex parse, as Bin(8)');
		} else {
			Output:line('[FAIL] bases: \'' . hex . '\', ' . parsed . ', \'' . bits . '\'');
		}

		# Case 5: as Int on String parses base 10.
		local Int is num: '1234' as Int;
		if (num == 1234) {
			Output:line('[PASS] String as Int: 1234');
		} else {
			Output:line('[FAIL] String as Int: ' . num);
		}

		# Case 6: generated toString - class instances render their class name.
		local String is label: 'instance: ' . dog;
		if (label == 'instance: Dog') {
			Output:line('[PASS] toString: class renders as Dog');
		} else {
			Output:line('[FAIL] toString: \'' . label . '\'');
		}

		# Case 7: enum variants render their variant name.
		local Color is c: Color:GREEN;
		local String is colorLine: 'color: ' . c;
		if (colorLine == 'color: GREEN') {
			Output:line('[PASS] enum render: variant name GREEN');
		} else {
			Output:line('[FAIL] enum render: \'' . colorLine . '\'');
		}

		# Case 8: explicit String cast matches concat behavior.
		local String is explicit: dog as String;
		if (explicit == 'Dog') {
			Output:line('[PASS] as String: Dog');
		} else {
			Output:line('[FAIL] as String: \'' . explicit . '\'');
		}

		# Case 9: checked downcast from Any to Dog
		local Any is anyDog: Dog:init();
		local Dog is checkedDog: anyDog as Dog;
		if (checkedDog:fetch() == 'ball') {
			Output:line('[PASS] checked downcast from Any: fetch = ball');
		} else {
			Output:line('[FAIL] checked downcast from Any: expected ball');
		}

		Output:line('=== End As Casts ===');
	}

}
