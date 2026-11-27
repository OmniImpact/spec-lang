#! specunit: helper

Class is DefArrHolder{
	replace [String] is namespace: ['test', 'lang', 'defaultarr'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['test', 'lang', 'defaultarr', DefArrItem]
	];

	Array of DefArrItem is items: Array();

	replace Function is init(Array of DefArrItem is items: Array()){
		:items: items;
	}
}
