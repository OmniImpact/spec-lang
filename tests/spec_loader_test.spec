#! Loader port check: multi-file loading, package resolution, the root
#! lattice preloads, implicit-Any parenting, and group-fragment merging.

Class is SpecLoaderTest{
	namespace: ['spec', 'test'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'loader', Loader],
		['spec', 'base', 'compiler', 'ast', ProgramNode],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['lib', 'base', 'io', Output],
		['lib', 'base', 'io', File]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Spec Loader Test ===');
		local Int is failures: 0;

		# A user program importing an io class by array-form package path.
		local String is src: "Class is Greeter{
	local String is greeting;
	Function is init(String is g){
		self:greeting: g;
	}
	replace Function of String is toString(){
		return 'Greeter(' . self:greeting . ')';
	}
}
Class of Greeter is LoudGreeter{
	replace Function of String is toString(){
		return 'LOUD ' . self:greeting;
	}
}
Class is LoaderE2E{
	replace Function is init(Map of String to String is args){
		local Greeter is g: LoudGreeter:init(g: 'hi');
		Output:line(text: g:toString());
	}
	replace Array of Array of String is using: [
		['lib', 'base', 'io', Output]
	];
}";
		File:write(path: 'tests/.loader_app_tmp.spec', content: src);

		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: 'tests/.loader_app_tmp.spec');

		# --- package resolution: imports loaded, lattice intact ---
		if (loader:loadedFileCount() >= 6
			&& loader:getParseErrors():length() == 0) {
			output:line('[PASS] multi-file load with zero errors');
		} else {
			output:line('[FAIL] load: files=' . (loader:loadedFileCount() as String) . ' errors=' . (loader:getParseErrors():length() as String));
			loader:getParseErrors():each(action: local Function(String is e){
				output:line(e);
			});
			failures: failures + 1;
		}

		# --- root lattice preloads + implicit Any ---
		local Loader is probe: Loader:init();
		local ProgramNode is classes: probe:loadProgram(rootPath: 'tests/.loader_app_tmp.spec');
		local LoaderE2EHelper is h: LoaderE2EHelper:init();
		if (h:hasClass(classes: classes, name: 'String')
			&& h:hasClass(classes: classes, name: 'Any')
			&& h:hasClass(classes: classes, name: 'Any')
			&& h:baseOf(classes: classes, name: 'LoudGreeter') == 'Greeter'
			&& h:baseOf(classes: classes, name: 'Greeter') == 'Any') {
			output:line('[PASS] root lattice and implicit Any');
		} else {
			output:line('[FAIL] lattice');
			failures: failures + 1;
		}

		# --- group fragments merge into their target ---
		File:write(path: 'tests/.loader_group_a_tmp.spec', content: "Class is Grouped{
	Function is init(Map of String to String is args){
	}
	replace Array of Array of String is group: [
		'Grouped'
	];
}");
		File:write(path: 'tests/.loader_group_b_tmp.spec', content: "Class is GroupedPart{
	Function of Int is answer(){
		return 42;
	}
	replace Array of Array of String is group: [
		'Grouped'
	];
}
Class is GroupMain{
	replace Function is init(Map of String to String is args){
	}
}");
		local Loader is gloader: Loader:init();
		local ProgramNode is gprog: gloader:loadProgram(rootPath: 'tests/.loader_group_a_tmp.spec');
		gloader:loadFile(filePath: 'tests/.loader_group_b_tmp.spec');
		gloader:mergeGroups();
		local LoaderE2EHelper is gh: LoaderE2EHelper:init();
		if (gloader:getParseErrors():length() == 0
			&& gh:hasClass(classes: gprog, name: 'Grouped')
			&& !gh:hasClass(classes: gprog, name: 'GroupedPart')
			&& gh:memberCount(classes: gprog, name: 'Grouped') == 2) {
			output:line('[PASS] group fragment merging');
		} else {
			output:line('[FAIL] group merge');
			failures: failures + 1;
		}

		# --- unresolvable imports are load errors ---
		File:write(path: 'tests/.loader_bad_tmp.spec', content: "Class is BadImporter{
	replace Function is init(Map of String to String is args){
	}
	replace Array of Array of String is using: [
		['no', 'such', 'Package']
	];
}");
		local Loader is bloader: Loader:init();
		bloader:loadProgram(rootPath: 'tests/.loader_bad_tmp.spec');
		if (bloader:getParseErrors():length() > 0) {
			output:line('[PASS] unresolvable import reported');
		} else {
			output:line('[FAIL] missing import error');
			failures: failures + 1;
		}

		File:remove(path: 'tests/.loader_app_tmp.spec');
		File:remove(path: 'tests/.loader_group_a_tmp.spec');
		File:remove(path: 'tests/.loader_group_b_tmp.spec');
		File:remove(path: 'tests/.loader_bad_tmp.spec');

		if (failures == 0) {
			output:line('[PASS] spec loader test complete');
		} else {
			output:line('[FAIL] spec loader test: ' . (failures as String) . ' failures');
		}
	}
}

## Test helper: class lookups over a loaded program.
Class is LoaderE2EHelper{
	namespace: ['spec', 'test'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', ProgramNode],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['lib', 'base', 'iterator']
	];

	Function of Boolean is hasClass(ProgramNode is classes, String is name){
		local Boolean is res: false;
		classes:classes:each(action: local Function(ClassInfo is c){
			if (c:name == name) {
				res: true;
			}
		});
		return res;
	}

	Function of String is baseOf(ProgramNode is classes, String is name){
		local String is res: '';
		classes:classes:each(action: local Function(ClassInfo is c){
			if (c:name == name) {
				res: c:baseClass;
			}
		});
		return res;
	}

	Function of Int is memberCount(ProgramNode is classes, String is name){
		local Int is res: 0;
		classes:classes:each(action: local Function(ClassInfo is c){
			if (c:name == name) {
				res: c:members:length();
			}
		});
		return res;
	}
}
