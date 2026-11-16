#! Package base:compiler:llvm
#! Plugin manifest and loader for CallLowerer subclasses.
##
## Spec's Introspection:instantiateSubclasses only discovers classes linked into
## the binary, so all concrete CallLowerer plugins live in this class's using:
## list and are loaded/sorted deterministically here.

Class is CallLowererRegistry{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', ControlFlowCallLowerer],
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', ConsoleCallLowerer],
		['base', 'compiler', 'llvm', ProcessCallLowerer],
		['base', 'compiler', 'llvm', FileCallLowerer],
		['base', 'compiler', 'llvm', DirCallLowerer],
		['base', 'compiler', 'llvm', NetAudioCallLowerer],
		['base', 'compiler', 'llvm', IntrospectionCallLowerer],
		['base', 'compiler', 'llvm', TimeCallLowerer],
		['base', 'compiler', 'llvm', MathCallLowerer],
		['base', 'compiler', 'llvm', MatchCallLowerer],
		['base', 'compiler', 'llvm', StringCallLowerer],
		['base', 'compiler', 'llvm', ArrayCallLowerer],
		['base', 'compiler', 'llvm', MapCallLowerer],
		['base', 'struct', Array],
		['base', 'struct', as Sort()],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
	}

	Function of Array of CallLowerer is loadAll(){
		local Array of Any is found: Introspection:instantiateSubclasses(baseName: 'CallLowerer');
		Sort:sortBy(values: found, compare: local Function of Int(Any is a, Any is b){
			local CallLowerer is ca: a as CallLowerer;
			local CallLowerer is cb: b as CallLowerer;
			if({ ca:order() != cb:order() }, { return ca:order() - cb:order(); });
			if({ ca:name() < cb:name() }, { return -1; });
			if({ ca:name() > cb:name() }, { return 1; });
			return 0;
		});
		local Array of CallLowerer is out: [];
		local Int is i: 0;
		while({ i < found:length() }, {
			out:add(item: found:get(index: i) as CallLowerer);
			i++;
		});
		return out;
	}
}
