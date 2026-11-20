#! specunit: negative
#! expect: Implicit return value in 'BadImplicitReturn:wrongType' has type 'String', expected 'Int'

Class is BadImplicitReturn{
	Function of Int is wrongType(){
		'not an int';
	}

	replace Function is init(){
	}
}
