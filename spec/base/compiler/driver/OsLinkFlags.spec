#! Package base:compiler:driver
#! OS-specific native linker flags for compiled Spec binaries.

Class of OsDispatch is OsLinkFlags{
	replace [String] is namespace: ['base', 'compiler', 'driver'];

	replace [[String]] is using: [
		['base', 'sys', OsDispatch],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	Boolean is pieOff: false;

	replace Function is init(){
		return;
	}

	replace Function is init(Boolean is noPie){
		:pieOff: noPie;
	}

	replace Function of String is linux(){
		return if({ :pieOff }, {
			'-ldl -no-pie'
		}, {
			'-ldl'
		});
	}

	replace Function of String is macos(){
		return '-framework AudioToolbox';
	}

	replace Function of String is windows(){
		return '-lws2_32 -lwinmm -lpsapi -Wl,-Bstatic,-lpthread,-Bdynamic';
	}

	Function of Array of String is flags(){
		return :value():split(delimiter: ' ');
	}
}
