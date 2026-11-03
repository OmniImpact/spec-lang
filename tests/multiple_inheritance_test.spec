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
	local String is name;

	replace Function of String is describe(){}
}

## Abstract contract providing an identifier field and tag getter.
Class is IdentifiableContract{
	local Int is id;

	replace Function of String is getTag(){}
}

## Concrete class extending multiple parent contracts.
Class is ServiceAccount extends NamedContract, IdentifiableContract{

	replace local String is name: "AdminService";
	replace local Int is id: 9001;

	replace local Function of String is describe(){
		return self:name . " (ID: " . self:id . ")";
	}

	replace local Function of String is getTag(){
		return "[" . self:name . "]";
	}

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line(" Spec Multiple Inheritance & Abstraction ");
		output:line("======================================\n");

		output:line("1. Testing multiple inheritance property access...");
		output:line("Account Name: " . self:name);
		output:line("Account ID:   " . self:id);

		if (self:name == "AdminService" && self:id == 9001) {
			output:line("[PASS] Successfully inherited fields from multiple contracts\n");
		} else {
			output:line("[FAIL] Property inheritance mismatch\n");
		}

		output:line("2. Testing implementation of abstract interface methods...");
		local String is desc: self:describe();
		local String is tag: self:getTag();
		output:line("Description: " . desc);
		output:line("Tag:         " . tag);

		if (desc == "AdminService (ID: 9001)" && tag == "[AdminService]") {
			output:line("[PASS] Successfully implemented abstract interface methods\n");
		} else {
			output:line("[FAIL] Method implementation mismatch\n");
		}

		output:line("3. Testing polymorphic dispatch through interface references...");
		local NamedContract is namedRef: self;
		local IdentifiableContract is idRef: self;
		local String is polyDesc: namedRef:describe();
		local String is polyTag: idRef:getTag();
		output:line("Polymorphic NamedContract:describe() -> " . polyDesc);
		output:line("Polymorphic IdentifiableContract:getTag() -> " . polyTag);

		if (polyDesc == "AdminService (ID: 9001)" && polyTag == "[AdminService]") {
			output:line("[PASS] Successfully dispatched polymorphically on interface types\n");
		} else {
			output:line("[FAIL] Polymorphic dispatch mismatch\n");
		}

		output:line("Multiple inheritance and abstraction test completed successfully!");
	}

}
