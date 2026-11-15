#! specunit: suite

Class of SpecUnitTest is TestHelloWorld{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		[Greeter]
	];

	Function is testGreet(){
		local Greeter is g: Greeter:init();
		Assert:areEqualString('Hello World', g:greet(greeting: 'Hello', name: 'World'));
		Assert:areEqualString('Hi User', g:greet(greeting: 'Hi', name: 'User'));
	}

}
