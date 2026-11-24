#! Package instimport:counter
#! Field-ful class for the instance-import regression test (E1/E2 full form).

Class is StatefulCounter{
	replace [String] is namespace: ['instimport', 'counter'];
	local Int is n: 0;
	local String is label: '';

	replace Function is init(String is label){
		:label: label;
	}

	replace Function is init(){
	}

	local Function of Int is hidden(Int is n){
		return n + 1000;
	}

	Function is tick(){
		:n: :n + 1;
	}

	Function of String is report(){
		return :label . '=' . (:n as String);
	}
}
