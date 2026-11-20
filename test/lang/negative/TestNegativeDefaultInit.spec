#! specunit: negative-suite

#! case: testMissingRequiredFieldInDefaultInit
#! expect: has no default value and is not assigned
Class is App{
	replace Function is init(Map of String to String is args){
		local ReqBox is b: ReqBox(titel: 'typo');
	}
}

Class is ReqBox{
	String is title;
}

#! case: testWrongTypeForRequiredFieldInDefaultInit
#! expect: has no default value and is not assigned
Class is App{
	replace Function is init(Map of String to String is args){
		local ReqBox is b: ReqBox(title: 123);
	}
}

Class is ReqBox{
	String is title;
}

#! case: testEmptyReplaceInitBlocksNamedArgs
#! expect: No signature of
Class is App{
	replace Function is init(Map of String to String is args){
		local SealedBox is b: SealedBox(x: 1);
	}
}

Class is SealedBox{
	Int is x: 0;

	replace Function is init(){
	}
}
