#! specunit: helper

Class is BetaUser{
	replace [String] is namespace: ['test', 'lang', 'pkgres', 'collision', 'beta'];

	replace [[String]] is using: [
		['test', 'lang', 'pkgres', 'collision', 'beta', DupType]
	];

	Function of String is run(){
		local DupType is d: DupType:SECOND;
		return d:value();
	}
}
