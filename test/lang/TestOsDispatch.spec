#! Tests for base:sys:OsDispatch abstract OS dispatch.

Class of SpecUnitTest is TestOsDispatch{
	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', OsDispatch],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()]
	];

	Function is testExplicitDispatch(){
		local SampleOsGreeting is g: SampleOsGreeting:init();
		Assert:areEqualString('hello-linux', g:forOs(os: 'linux'));
		Assert:areEqualString('hello-macos', g:forOs(os: 'macos'));
		Assert:areEqualString('hello-windows', g:forOs(os: 'windows'));
	}

	Function is testHostOsDispatch(){
		local SampleOsGreeting is g: SampleOsGreeting:init();
		local String is os: Process:osName();
		if({ os == 'windows' }, {
			Assert:areEqualString('hello-windows', g:value());
		}, {
			if({ os == 'macos' }, {
				Assert:areEqualString('hello-macos', g:value());
			}, {
				Assert:areEqualString('hello-linux', g:value());
			});
		});
	}
}

Class of OsDispatch is SampleOsGreeting{
	replace [[String]] is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function of String is linux(){
		return 'hello-linux';
	}

	replace Function of String is macos(){
		return 'hello-macos';
	}

	replace Function of String is windows(){
		return 'hello-windows';
	}
}
