#! Package base:scrap
#! Configuration descriptor for a single menu item inside a `MenuConfig`.

Class is MenuItemConfig{
	replace [String] is namespace: ['base', 'scrap'];

	String is id: '';
	String is label: '';
	Function is onClick: local Function(){};

	replace Function is init(String is id, String is label, Function is onClick: local Function(){}){
		:id: id;
		:label: label;
		:onClick: onClick;
	}
}
