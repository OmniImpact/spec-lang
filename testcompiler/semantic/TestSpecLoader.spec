#! Loader port check: multi-file loading, package resolution, the root
#! lattice preloads and implicit-Any parenting.

Class of SpecUnitTest is TestSpecLoader{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'sys', as File()]
	];

	Function of String is sampleAppSource(){
		return "Class is Greeter{
	local String is greeting;
	Function is init(String is g){
		:greeting: g;
	}
	replace Function of String is toString(){
		return 'Greeter(' . :greeting . ')';
	}
}
Class of Greeter is LoudGreeter{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
	replace Function of String is toString(){
		return 'LOUD ' . :greeting;
	}
}
Class is LoaderE2E{
	replace Function is init(Map of String to String is args){
		local Greeter is g: LoudGreeter:init(g: 'hi');
		Output:line(text: g:toString());
	}
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
}";
	}

	Function is testMultiFileLoadWithZeroErrors(){
		fileWrite(path: 'testcompiler/semantic/.loader_app_tmp.spec', content: :sampleAppSource());

		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: 'testcompiler/semantic/.loader_app_tmp.spec');

		Assert:isTrue(loader:loadedFileCount() >= 6);
		Assert:areEqualInt(0, loader:getParseErrors():length());

		fileRemove(path: 'testcompiler/semantic/.loader_app_tmp.spec');
	}

	Function is testRootLatticeAndImplicitAny(){
		fileWrite(path: 'testcompiler/semantic/.loader_app_tmp.spec', content: :sampleAppSource());

		local Loader is probe: Loader:init();
		local ProgramNode is classes: probe:loadProgram(rootPath: 'testcompiler/semantic/.loader_app_tmp.spec');
		local LoaderE2EHelper is h: LoaderE2EHelper:init();

		Assert:isTrue(h:hasClass(classes: classes, name: 'String'));
		Assert:isTrue(h:hasClass(classes: classes, name: 'Any'));
		Assert:isTrue(h:hasClass(classes: classes, name: 'Class'));
		Assert:areEqualString('Greeter', h:baseOf(classes: classes, name: 'LoudGreeter'));
		Assert:areEqualString('Class', h:baseOf(classes: classes, name: 'Greeter'));
		Assert:areEqualString('Stringable', h:baseOf(classes: classes, name: 'Class'));
		Assert:areEqualString('Loadable', h:baseOf(classes: classes, name: 'Stringable'));
		Assert:isTrue(h:baseOf(classes: classes, name: 'Loadable') == 'Any' || h:baseOf(classes: classes, name: 'Loadable') == 'base:sysinternal:Loadable');

		fileRemove(path: 'testcompiler/semantic/.loader_app_tmp.spec');
	}

	Function is testUnresolvableImportReported(){
		fileWrite(path: 'testcompiler/semantic/.loader_bad_tmp.spec', content: "Class is BadImporter{
	replace Function is init(Map of String to String is args){
	}
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['no', 'such', 'Package'],
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
}");
		local Loader is bloader: Loader:init();
		bloader:loadProgram(rootPath: 'testcompiler/semantic/.loader_bad_tmp.spec');

		Assert:isTrue(bloader:getParseErrors():length() > 0);

		fileRemove(path: 'testcompiler/semantic/.loader_bad_tmp.spec');
	}
}

## Test helper: class lookups over a loaded program.
Class is LoaderE2EHelper{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'iterator'],
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];

	Function of Boolean is hasClass(ProgramNode is classes, String is name){
		local Boolean is res: false;
		while([Int is ci: 0], { !res && ci < classes:classes:length() }, {
			Conditional:if(check: { classes:classes:get(index: ci):name == name }, then: {
				res: true;
			});
			ci++;
		});
		return res;
	}

	Function of String is baseOf(ProgramNode is classes, String is name){
		local String is res: '';
		while([Int is ci: 0], { ci < classes:classes:length() }, {
			local ClassInfo is c: classes:classes:get(index: ci);
			Conditional:if(check: { c:name == name }, then: {
				res: c:baseClass;
			});
			ci++;
		});
		return res;
	}

	Function of Int is memberCount(ProgramNode is classes, String is name){
		local Int is res: 0;
		while([Int is ci: 0], { ci < classes:classes:length() }, {
			local ClassInfo is c: classes:classes:get(index: ci);
			Conditional:if(check: { c:name == name }, then: {
				res: c:members:length();
			});
			ci++;
		});
		return res;
	}
}
