## Minimal greeting application demonstrating CLI arguments and utility delegation.
Class is HelloWorld{

	local Str is greeting: 'Hello';

	replace [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Process()]],
		['base', 'sys', as Conditional()],
		[Greeter]
	];

	## Entry point; reads optional [args] `'name'` and prints the formatted greeting.
	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/helloworld/cli.json');
		if({ !cli:parse(rawArgs: rawArgs()) }, {
			if({ cli:helpRequested || cli:versionRequested }, { return; });
			exit(status: 1);
		});
		local String is name: cli:getString(name: 'name', default: 'User');
		local Greeter is greeter: Greeter();
		line(greeter:greet(greeting: greeting, name: name));
	}

}
