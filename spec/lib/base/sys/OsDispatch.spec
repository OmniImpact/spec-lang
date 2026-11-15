#! Package base:sys
#! Abstract base class for OS-specific dispatch.
##
## Subclasses must implement linux(), macos(), and windows(); leaving any of
## them unimplemented is a compile-time type error. Call value() to evaluate
## the implementation for the current host OS, or forOs(os:) to test/dispatch
## explicitly.

Class is OsDispatch{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	Function of String is linux();
	Function of String is macos();
	Function of String is windows();

	Function of String is forOs(String is os){
		if({ os == 'windows' }, { return self:windows(); });
		if({ os == 'macos' }, { return self:macos(); });
		return self:linux();
	}

	Function of String is value(){
		return self:forOs(os: Process:osName());
	}
}
