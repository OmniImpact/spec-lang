#! SpecUnit sweep (from multiple_inheritance_test.spec): multiple
#! inheritance and interface abstraction — classes with uninitialized
#! fields act as contracts, comma-separated parents assemble, abstract
#! fields/methods are implemented on the concrete child, and interface-
#! typed references dispatch polymorphically.

Class of SpecUnitTest is TestMultipleInheritance{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testInheritedFieldsFromContracts(){
		local ServiceAccount is svc: ServiceAccount:init();
		Assert:areEqualString('AdminService', svc:name);
		Assert:areEqualInt(9001, svc:id);
	}

	Function is testAbstractMethodsImplemented(){
		local ServiceAccount is svc: ServiceAccount:init();
		Assert:areEqualString('AdminService (ID: 9001)', svc:describe());
		Assert:areEqualString('[AdminService]', svc:getTag());
	}

	Function is testPolymorphicDispatchOnInterfaceTypes(){
		local ServiceAccount is svc: ServiceAccount:init();
		local NamedContract is namedRef: svc;
		local IdentifiableContract is idRef: svc;
		Assert:areEqualString('AdminService (ID: 9001)', namedRef:describe());
		Assert:areEqualString('[AdminService]', idRef:getTag());
	}
}

## Abstract contract providing a name field and description method.
Class is NamedContract{
	String is name;

	Function of String is describe(){}
}

## Abstract contract providing an identifier field and tag getter.
Class is IdentifiableContract{
	Int is id;

	Function of String is getTag(){}
}

## Concrete class extending multiple parent contracts.
Class of NamedContract, IdentifiableContract is ServiceAccount{
	replace String is name: 'AdminService';
	replace Int is id: 9001;

	replace Function of String is describe(){
		return self:name . ' (ID: ' . self:id . ')';
	}

	replace Function of String is getTag(){
		return '[' . self:name . ']';
	}
}
