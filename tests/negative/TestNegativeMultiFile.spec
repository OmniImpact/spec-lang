Class of SpecUnitTest is TestNegativeMultiFile{
	replace Array of Array of String is using: [
		['specunit', Assert],
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testInstanceCycle(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/instancecycle/cycroot.spec',
			expect: 'Instance import cycle: A -> B -> A'
		);
	}

	Function is testUnimportedTypeGate(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/n18gate/n18_unimported_type_negative_test.spec',
			expect: "'GTarget' is not imported by 'N18UnimportedType'"
		);
	}

	Function is testImportLocalMember(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/n24_import_local_member.spec',
			expect: "is local to class 'StatefulCounter' and cannot be accessed from 'WallProbe'"
		);
	}

	Function is testInnerNameCollision(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/n25_inner_name_collision.spec',
			expect: "Type 'Helper' is provided by LibA:Helper and LibB:Helper; qualify the reference"
		);
	}

	Function is testFieldThroughImport(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/n26_field_through_import.spec',
			expect: "Fields are not reachable through the class-name prefix 'FieldDep'"
		);
	}

	Function is testAsFormDefault(){
		Assert:compilerRejectsFile(
			filePath: 'tests/negative/fixtures/n29_as_form_default.spec',
			expect: "'Math2' is not imported by 'N29AsFormDefault'"
		);
	}
}
