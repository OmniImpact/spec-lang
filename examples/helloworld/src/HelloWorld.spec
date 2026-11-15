Class is HelloWorld{

	local String is greeting: 'Hello';

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		[Greeter]
	];

	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		local Greeter is greeter: Greeter:init();
		line(greeter:greet(greeting: self:greeting, name: name));
	}

}
