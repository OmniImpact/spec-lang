#! specunit: helper

Class is AlphaUser{
	replace [String] is namespace: ['test', 'lang', 'pkgres', 'collision', 'alpha'];

	replace [[String]] is using: [
		['test', 'lang', 'pkgres', 'collision', 'alpha', DupType]
	];

	Function of Int is run(){
		local DupType is d: DupType(x: 42);
		return d:value();
	}
}
