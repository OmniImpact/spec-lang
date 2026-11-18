#! SpecUnit sweep (from as_cast_test.spec): the `as` cast operator across
#! classes, numerics, and base pseudo-types.

Class of SpecUnitTest is TestAsCast{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testUpcastDispatch(){
		local Dog is dog: Dog:init();
		local Animal is asAnimal: dog as Animal;
		Assert:areEqualString('woof', asAnimal:speak());
	}

	Function is testDowncastReach(){
		local Dog is dog: Dog:init();
		local Animal is asAnimal: dog as Animal;
		local Dog is back: asAnimal as Dog;
		Assert:areEqualString('ball', back:fetch());
	}

	Function is testNumericCasts(){
		local Int is truncated: 3.9 as Int;
		local Float is widened: 7 as Float;
		Assert:areEqualInt(3, truncated);
		Assert:areClose(7.0, widened, 0.001);
	}

	Function is testBaseFormats(){
		local String is hex: 65516 as Hex;
		local Int is parsed: 'ffec' as Hex;
		local String is bits: 10 as Bin(8);
		Assert:areEqualString('ffec', hex);
		Assert:areEqualInt(65516, parsed);
		Assert:areEqualString('00001010', bits);
	}

	Function is testStringAsInt(){
		local Int is num: '1234' as Int;
		Assert:areEqualInt(1234, num);
	}

	Function is testToStringRenders(){
		local Dog is dog: Dog:init();
		local String is label: 'instance: ' . dog;
		Assert:areEqualString('instance: Dog', label);
	}

	Function is testEnumRender(){
		local Color is c: Color:GREEN;
		local String is colorLine: 'color: ' . c;
		Assert:areEqualString('color: GREEN', colorLine);
	}

	Function is testExplicitStringCast(){
		local Dog is dog: Dog:init();
		local String is explicit: dog as String;
		Assert:areEqualString('Dog', explicit);
	}

	Function is testCheckedDowncastFromAny(){
		local Any is anyDog: Dog:init();
		local Dog is checkedDog: anyDog as Dog;
		Assert:areEqualString('ball', checkedDog:fetch());
	}
}
Enum is Color {
	RED,
	GREEN
}

Class is Animal{

	Function of String is speak(){
		return '...';
	}
}

Class of Animal is Dog{

	replace Function of String is speak(){
		return 'woof';
	}

	Function of String is fetch(){
		return 'ball';
	}
}

