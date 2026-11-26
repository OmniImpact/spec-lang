#! Package base:scrap
#! Configuration descriptor for a menu item (or submenu parent) inside a `MenuConfig`.

Class is MenuItemConfig{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'struct', Array]
	];

	String is id: '';
	String is label: '';
	Function is onClick: local Function(){};
	Boolean is checked: false;
	Array of MenuItemConfig is subItems: Array();

	replace Function is init(
		String is id,
		String is label,
		Function is onClick: local Function(){},
		Boolean is checked: false
	){
		:id: id;
		:label: label;
		:onClick: onClick;
		:checked: checked;
		subItems: Array();
	}

	Function is addSubItem(MenuItemConfig is item){
		subItems:add(item: item);
	}
}
