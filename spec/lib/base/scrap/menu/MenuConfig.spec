#! Package base:scrap
#! Configuration descriptor for a top-level menu inside a `ToolbarConfig`.

Class is MenuConfig{
	replace [String] is namespace: ['base', 'scrap', 'menu'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'menu', MenuItemConfig]
	];

	String is id: '';
	String is label: '';
	Array of MenuItemConfig is items: Array();

	replace Function is init(String is id, String is label){
		:id: id;
		:label: label;
		items: Array();
	}

	Function is addItem(MenuItemConfig is item){
		items:add(item: item);
	}
}
