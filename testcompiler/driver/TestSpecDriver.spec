#! Driver + CompilationReport check: the new driver compiles a source
#! file end to end (load, check, generate, cc) and its checker rejects
#! invalid programs.

Class of SpecUnitTest is TestSpecDriver{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'driver', Driver],
		['base', 'struct', Map],
		['base', 'sys', as File()]
	];

	Function is testDriverEmitsCWithVtableDispatch(){
		local String is src: "Class is Greeter{
	local String is greeting;
	replace Function is init(String is g){
		self:greeting: g;
	}
	Function of String is text(){
		return self:greeting;
	}
	replace Function of String is toString(){
		return 'Greeter(' . self:text() . ')';
	}
}
Class of Greeter is LoudGreeter{

	replace Array of Array of String is using: [
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
	replace Function of String is toString(){
		return 'LOUD ' . self:text();
	}
}
Class is DriverE2E{
	replace Function is init(Map of String to String is args){
		local Greeter is g: LoudGreeter:init(g: 'hi');
		Output:line(text: g:toString());
	}
	replace Array of Array of String is using: [
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
}";
		fileWrite(path: 'testcompiler/driver/.driver_app_tmp.spec', content: src);

		local Map of String to String is cli: Map:init();
		cli:set(key: 'i', value: 'testcompiler/driver/.driver_app_tmp.spec');
		cli:set(key: 'emit-llvm', value: 'testcompiler/driver/.driver_app_tmp.ll');
		cli:set(key: 'quiet', value: 'true');
		local Driver is d: Driver:init(args: cli);

		local String is llSrc: fileRead(path: 'testcompiler/driver/.driver_app_tmp.ll', default: '');
		Assert:isTrue(llSrc:contains(needle: '@main('));
		Assert:isTrue(llSrc:contains(needle: 'LoudGreeter_toString'));
		Assert:isTrue(llSrc:contains(needle: '@.vtable.LoudGreeter'));

		fileRemove(path: 'testcompiler/driver/.driver_app_tmp.ll');
		fileRemove(path: 'testcompiler/driver/.driver_app_tmp.spec');
	}
}
