#! Package base:scrap
#! Configuration object pushed into a `ToolbarContainer` to populate a `Toolbar`.

Class is ToolbarConfig{
	replace [String] is namespace: ['base', 'scrap', 'toolbar'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'menu', MenuConfig]
	];

	Array of MenuConfig is menus: Array();
	Float is heightPt: 19.0;
	String is radioOffIconSvg: '';
	String is radioOnIconSvg: '';
	String is checkboxOffIconSvg: '';
	String is checkboxOnIconSvg: '';

	replace Function is init(
		Float is heightPt: 19.0,
		String is radioOffIconSvg: '',
		String is radioOnIconSvg: '',
		String is checkboxOffIconSvg: '',
		String is checkboxOnIconSvg: ''
	){
		menus: Array();
		:heightPt: heightPt;
		:radioOffIconSvg: radioOffIconSvg;
		:radioOnIconSvg: radioOnIconSvg;
		:checkboxOffIconSvg: checkboxOffIconSvg;
		:checkboxOnIconSvg: checkboxOnIconSvg;
	}

	Function is addMenu(MenuConfig is menu){
		menus:add(item: menu);
	}
}
