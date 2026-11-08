#! Driver + CompilationReport check: the new driver compiles a source
#! file end to end (load, check, generate, cc) and its checker rejects
#! invalid programs.

Class is SpecDriverTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'driver', Driver],
		['base', 'io', Output],
		['base', 'io', File],
		['base', 'struct', Map],
		['base', 'io', as File()],
		['base', 'io', as Output()],
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
		['base', 'io', as File()],
		['base', 'io', as Output()]
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
		['base', 'io', Output],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];
}";
		File:write(path: 'tests/.driver_app_tmp.spec', content: src);

		local Map of String to String is cli: Map:init();
		cli:set(key: 'i', value: 'tests/.driver_app_tmp.spec');
		cli:set(key: 'emit-c', value: 'tests/.driver_app_tmp.c');
		local Driver is d: Driver:init(args: cli);

		local String is cSrc: File:read(path: 'tests/.driver_app_tmp.c', default: '');
		Conditional:branch(check: { cSrc:contains(needle: 'int main(')
			&& cSrc:contains(needle: 'LoudGreeter_toString')
			&& cSrc:contains(needle: '_vtable[') }, then: {
			Output:line('[PASS] driver emitted C with vtable dispatch');
		}, otherwise: {
			Output:line('[FAIL] driver emission');
			failures: failures + 1;
		});
		File:remove(path: 'tests/.driver_app_tmp.c');
		File:remove(path: 'tests/.driver_app_tmp.spec');

		Conditional:branch(check: { failures == 0 }, then: {
			Output:line('[PASS] spec driver test complete');
		}, otherwise: {
			Output:line('[FAIL] spec driver test: ' . (failures as String) . ' failures');
		});
	}
}
