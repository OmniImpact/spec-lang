#! Package base:scrap
#! Configuration descriptor for a menu item (or submenu parent) inside a `MenuConfig`.

Class is MenuItemConfig{
	replace [String] is namespace: ['base', 'scrap', 'menu'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'menu', MenuItemKind]
	];

	String is id: '';
	String is label: '';
	Function is onClick: local Function(){};
	Boolean is checked: false;
	Boolean is enabled: true;
	MenuItemKind is kind: MenuItemKind:ACTION;
	String is iconSvg: '';
	Array of MenuItemConfig is subItems: Array();

	replace Function is init(
		String is id,
		String is label,
		Function is onClick: local Function(){},
		Boolean is checked: false,
		Boolean is enabled: true,
		MenuItemKind is kind: MenuItemKind:ACTION,
		String is iconSvg: '',
		Array of MenuItemConfig is subItems: Array()
	){
		:id: id;
		:label: label;
		:onClick: onClick;
		:checked: checked;
		:enabled: enabled;
		:kind: kind;
		:iconSvg: iconSvg;
		:subItems: Array();
		local Int is si: 0;
		while({ si < subItems:length() }, {
			:subItems:add(item: subItems:get(index: si));
			si: si + 1;
		});
	}

	Function is addSubItem(MenuItemConfig is item){
		subItems:add(item: item);
	}
}
