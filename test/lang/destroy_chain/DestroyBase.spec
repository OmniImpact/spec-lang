#! specunit: helper

Class is DestroyBase{
	replace [String] is namespace: ['test', 'lang', 'destroy_chain'];

	replace [[String]] is using: [
		['base', 'struct', Array]
	];

	held Array of String is log: Array();

	Function is destroy(){
		DestroyBase:log:add(item: 'base');
	}
}
