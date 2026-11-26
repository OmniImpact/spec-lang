#! Package base:scrap
#! Configuration object pushed into a `ToolbarContainer` to populate a `Toolbar`.

Class is ToolbarConfig{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', MenuConfig]
	];

	Array of MenuConfig is menus: Array();
	Float is heightPt: 30.0;

	replace Function is init(Float is heightPt: 30.0){
		menus: Array();
		:heightPt: heightPt;
	}

	Function is addMenu(MenuConfig is menu){
		menus:add(item: menu);
	}
}
