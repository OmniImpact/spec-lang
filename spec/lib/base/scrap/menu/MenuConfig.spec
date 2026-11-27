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
	Boolean is visible: true;
	Array of MenuItemConfig is items: Array();

	replace Function is init(
		String is id,
		String is label,
		Boolean is visible: true,
		Array of MenuItemConfig is items: Array()
	){
		:id: id;
		:label: label;
		:visible: visible;
		:items: items;
	}

	Function is addItem(MenuItemConfig is item){
		items:add(item: item);
	}
}
