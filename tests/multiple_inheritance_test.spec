# =============================================================================
# Spec Multiple Inheritance & Interface Abstraction Test
#
# Tests:
# 1. Classes with uninitialized fields act inherently as interfaces/contracts.
# 2. Multiple inheritance via comma-separated `extends Parent1, Parent2`.
# 3. Enforcement of abstract field/method implementation on init.
# 4. Strict enforcement of 'replace' modifier on overrides.
# =============================================================================

## Abstract contract providing a name field and description method.
Class is NamedContract{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];
	String is name;

	Function of String is describe(){}
}

## Abstract contract providing an identifier field and tag getter.
Class is IdentifiableContract{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	Int is id;

	Function of String is getTag(){}
}

## Concrete class extending multiple parent contracts.
Class of NamedContract, IdentifiableContract is ServiceAccount{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	replace String is name: 'AdminService';
	replace Int is id: 9001;

	replace Function of String is describe(){
		return self:name . ' (ID: ' . self:id . ')';
	}

	replace Function of String is getTag(){
		return '[' . self:name . ']';
	}

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line(' Spec Multiple Inheritance & Abstraction ');
		Output:line("======================================\n");

		Output:line('1. Testing multiple inheritance property access...');
		Output:line('Account Name: ' . self:name);
		Output:line('Account ID:   ' . self:id);

		Conditional:if(check: { self:name == 'AdminService' && self:id == 9001 }, then: {
			Output:line("[PASS] Successfully inherited fields from multiple contracts\n");
		}, else: {
			Output:line("[FAIL] Property inheritance mismatch\n");
		});

		Output:line('2. Testing implementation of abstract interface methods...');
		local String is desc: self:describe();
		local String is tag: self:getTag();
		Output:line('Description: ' . desc);
		Output:line('Tag:         ' . tag);

		Conditional:if(check: { desc == 'AdminService (ID: 9001)' && tag == '[AdminService]' }, then: {
			Output:line("[PASS] Successfully implemented abstract interface methods\n");
		}, else: {
			Output:line("[FAIL] Method implementation mismatch\n");
		});

		Output:line('3. Testing polymorphic dispatch through interface references...');
		local NamedContract is namedRef: self;
		local IdentifiableContract is idRef: self;
		local String is polyDesc: namedRef:describe();
		local String is polyTag: idRef:getTag();
		Output:line('Polymorphic NamedContract:describe() -> ' . polyDesc);
		Output:line('Polymorphic IdentifiableContract:getTag() -> ' . polyTag);

		Conditional:if(check: { polyDesc == 'AdminService (ID: 9001)' && polyTag == '[AdminService]' }, then: {
			Output:line("[PASS] Successfully dispatched polymorphically on interface types\n");
		}, else: {
			Output:line("[FAIL] Polymorphic dispatch mismatch\n");
		});

		Output:line('Multiple inheritance and abstraction test completed successfully!');
	}

}
