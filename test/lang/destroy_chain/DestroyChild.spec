#! specunit: helper

Class of DestroyBase is DestroyChild{
	replace [String] is namespace: ['test', 'lang', 'destroy_chain'];

	replace [[String]] is using: [
		['test', 'lang', 'destroy_chain', DestroyBase]
	];

	replace Function is destroy(){
		DestroyBase:log:add(item: 'child');
	}
}
