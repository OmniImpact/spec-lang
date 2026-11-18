#! Package base:sys
#! Abstract base class for OS-specific dispatch.
##
## Subclasses must implement linux(), macos(), and windows(); leaving any of
## them unimplemented is a compile-time type error. Call value() to evaluate
## the implementation for the current host OS, forOs(os:) to test/dispatch
## explicitly, or getOsBlock(separatePosix:) to emit a C preprocessor block.

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
		return if({ os == 'windows' }, {
			:windows()
		}, {
			if({ os == 'macos' }, { :macos() }, { :linux() })
		});
	}

	Function of String is value(){
		return :forOs(os: Process:osName());
	}

	Function of String is getOsBlock(Boolean is separatePosix: false){
		local String is win: :windows();
		local String is lin: :linux();
		return if({ separatePosix }, {
			local String is mac: :macos();
			"#if defined(_WIN32)\n" . win . "\n#elif defined(__APPLE__) && defined(__MACH__)\n" . mac . "\n#elif defined(__linux__)\n" . lin . "\n#endif"
		}, {
			if({ lin == '' }, {
				"#if defined(_WIN32)\n" . win . "\n#endif"
			}, {
				if({ win == '' }, {
					"#if !defined(_WIN32)\n" . lin . "\n#endif"
				}, {
					"#if defined(_WIN32)\n" . win . "\n#else\n" . lin . "\n#endif"
				})
			})
		});
	}
}
