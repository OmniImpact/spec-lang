#! Loader port check: multi-file loading, package resolution, the root
#! lattice preloads and implicit-Any parenting.

Class is SpecLoaderTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'io', Output],
		['base', 'io', File],
		['base', 'io', as File()],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Loader Test ===');
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

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];
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
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];
}";
		File:write(path: 'tests/.loader_app_tmp.spec', content: src);

		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: 'tests/.loader_app_tmp.spec');

		# --- package resolution: imports loaded, lattice intact ---
		Conditional:if(check: { loader:loadedFileCount() >= 6
			&& loader:getParseErrors():length() == 0 }, then: {
			Output:line('[PASS] multi-file load with zero errors');
		}, else: {
			Output:line('[FAIL] load: files=' . (loader:loadedFileCount() as String) . ' errors=' . (loader:getParseErrors():length() as String));
			loader:getParseErrors():each(action: local Function(String is e){
				Output:line(e);
			});
			failures: failures + 1;
		});

		# --- root lattice preloads + implicit Any ---
		local Loader is probe: Loader:init();
		local ProgramNode is classes: probe:loadProgram(rootPath: 'tests/.loader_app_tmp.spec');
		local LoaderE2EHelper is h: LoaderE2EHelper:init();
		Conditional:if(check: { h:hasClass(classes: classes, name: 'String')
			&& h:hasClass(classes: classes, name: 'Any')
			&& h:hasClass(classes: classes, name: 'Any')
			&& h:baseOf(classes: classes, name: 'LoudGreeter') == 'Greeter'
			&& h:baseOf(classes: classes, name: 'Greeter') == 'Any' }, then: {
			Output:line('[PASS] root lattice and implicit Any');
		}, else: {
			Output:line('[FAIL] lattice');
			failures: failures + 1;
		});

		# --- unresolvable imports are load errors ---
		File:write(path: 'tests/.loader_bad_tmp.spec', content: "Class is BadImporter{
	replace Function is init(Map of String to String is args){
	}
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['no', 'such', 'Package'],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];
}");
		local Loader is bloader: Loader:init();
		bloader:loadProgram(rootPath: 'tests/.loader_bad_tmp.spec');
		Conditional:if(check: { bloader:getParseErrors():length() > 0 }, then: {
			Output:line('[PASS] unresolvable import reported');
		}, else: {
			Output:line('[FAIL] missing import error');
			failures: failures + 1;
		});

		File:remove(path: 'tests/.loader_app_tmp.spec');
		File:remove(path: 'tests/.loader_bad_tmp.spec');

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] spec loader test complete');
		}, else: {
			Output:line('[FAIL] spec loader test: ' . (failures as String) . ' failures');
		});
	}
}

## Test helper: class lookups over a loaded program.
Class is LoaderE2EHelper{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'iterator'],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];

	Function of Boolean is hasClass(ProgramNode is classes, String is name){
		local Boolean is res: false;
		classes:classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:name == name }, then: {
				res: true;
			});
		});
		return res;
	}

	Function of String is baseOf(ProgramNode is classes, String is name){
		local String is res: '';
		classes:classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:name == name }, then: {
				res: c:baseClass;
			});
		});
		return res;
	}

	Function of Int is memberCount(ProgramNode is classes, String is name){
		local Int is res: 0;
		classes:classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:name == name }, then: {
				res: c:members:length();
			});
		});
		return res;
	}
}
