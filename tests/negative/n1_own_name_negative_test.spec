#! specunit: negative
#! expect: through the class name inside 'N1SelfRead' itself; use self

#! N1/N9: the own-class-name receiver inside the class passes NULL self
#! (the D1-family trap) and is banned outright (§2.2).

Class is N1SelfRead {
	local Int is count: 5;

	Function of Int is bump() {
		return self:count + 1;
	}

	replace Function is init(Map of String to String is args) {
		local Int is v: N1SelfRead:bump();
		Output:line((v as String));
	}
}
