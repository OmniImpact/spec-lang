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
	Function of String is speak(){
		return "...";
	}
}

Class of Animal is Dog{
	replace Function of String is speak(){
		return "woof";
	}

	Function of String is fetch(){
		return "ball";
	}
}

Class is AsCastTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: As Casts ===");

		# Case 1: upcast - dog passed and stored as Animal, dispatch stays virtual.
		local Dog is dog: Dog:init();
		local Animal is asAnimal: dog as Animal;
		if (asAnimal:speak() == "woof") {
			output:line("[PASS] upcast: virtual dispatch preserved");
		} else {
			output:line("[FAIL] upcast: expected woof");
		}

		# Case 2: downcast - Animal reference back to Dog, subclass method reachable.
		local Dog is back: asAnimal as Dog;
		if (back:fetch() == "ball") {
			output:line("[PASS] downcast: subclass method reachable");
		} else {
			output:line("[FAIL] downcast: expected ball");
		}

		# Case 3: numeric casts.
		local Int is truncated: 3.9 as Int;
		local Float is widened: 7 as Float;
		if (truncated == 3 && widened == 7.0) {
			output:line("[PASS] numeric: 3.9 as Int = 3, 7 as Float = 7.0");
		} else {
			output:line("[FAIL] numeric: " . truncated . ", " . widened);
		}

		# Case 4: base format and parse via pseudo-types.
		local String is hex: 65516 as Hex;
		local Int is parsed: "ffec" as Hex;
		local String is bits: 10 as Bin(8);
		if (hex == "ffec" && parsed == 65516 && bits == "00001010") {
			output:line("[PASS] bases: as Hex, as Hex parse, as Bin(8)");
		} else {
			output:line("[FAIL] bases: '" . hex . "', " . parsed . ", '" . bits . "'");
		}

		# Case 5: as Int on String parses base 10.
		local Int is num: "1234" as Int;
		if (num == 1234) {
			output:line("[PASS] String as Int: 1234");
		} else {
			output:line("[FAIL] String as Int: " . num);
		}

		# Case 6: generated toString - class instances render their class name.
		local String is label: "instance: " . dog;
		if (label == "instance: Dog") {
			output:line("[PASS] toString: class renders as Dog");
		} else {
			output:line("[FAIL] toString: '" . label . "'");
		}

		# Case 7: enum variants render their variant name.
		local Color is c: Color:GREEN;
		local String is colorLine: "color: " . c;
		if (colorLine == "color: GREEN") {
			output:line("[PASS] enum render: variant name GREEN");
		} else {
			output:line("[FAIL] enum render: '" . colorLine . "'");
		}

		# Case 8: explicit String cast matches concat behavior.
		local String is explicit: dog as String;
		if (explicit == "Dog") {
			output:line("[PASS] as String: Dog");
		} else {
			output:line("[FAIL] as String: '" . explicit . "'");
		}

		output:line("=== End As Casts ===");
	}

}
