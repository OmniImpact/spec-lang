#! specunit: helper

Class is DefArrItem{
	replace [String] is namespace: ['test', 'lang', 'defaultarr'];

	String is label: '';

	replace Function is init(String is label: ''){
		:label: label;
	}
}
