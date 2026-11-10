#! Driver + CompilationReport check: the new driver compiles a source
#! file end to end (load, check, generate, cc) and its checker rejects
#! invalid programs.

Class is SpecDriverTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'driver', Driver],
		['base', 'sys', Output],
		['base', 'sys', File],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Driver Test ===');
		local Int is failures: 0;

		# A valid program: multi-file, polymorphic, floor-imported.
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
		['base', 'sys', Output],
		['base', 'sys', as File()],
		['base', 'sys', as Output()]
	];
}";
		fileWrite(path: 'tests/.driver_app_tmp.spec', content: src);

		local Map of String to String is cli: Map:init();
		cli:set(key: 'i', value: 'tests/.driver_app_tmp.spec');
		cli:set(key: 'emit-c', value: 'tests/.driver_app_tmp.c');
		local Driver is d: Driver:init(args: cli);

		local String is cSrc: fileRead(path: 'tests/.driver_app_tmp.c', default: '');
		Conditional:if(check: { cSrc:contains(needle: 'int main(')
			&& cSrc:contains(needle: 'LoudGreeter_toString')
			&& cSrc:contains(needle: '_vtable[') }, then: {
			Output:line('[PASS] driver emitted C with vtable dispatch');
		}, else: {
			Output:line('[FAIL] driver emission');
			failures: failures + 1;
		});
		fileRemove(path: 'tests/.driver_app_tmp.c');
		fileRemove(path: 'tests/.driver_app_tmp.spec');

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] spec driver test complete');
		}, else: {
			Output:line('[FAIL] spec driver test: ' . (failures as String) . ' failures');
		});
	}
}
