#! Package base:scrap
#! Configuration object pushed into a `ToolbarContainer` to populate a `Toolbar`.

Class is ToolbarConfig{
	replace [String] is namespace: ['base', 'scrap', 'toolbar'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'scrap', 'menu', MenuConfig]
	];

	held String is DEFAULT_RADIO_OFF_SVG: "<svg viewBox=\"0 0 16 16\"><circle cx=\"8\" cy=\"8\" r=\"5.5\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.5\"/></svg>";
	held String is DEFAULT_RADIO_ON_SVG: "<svg viewBox=\"0 0 16 16\"><circle cx=\"8\" cy=\"8\" r=\"5.5\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.5\"/><circle cx=\"8\" cy=\"8\" r=\"2.8\" fill=\"#ffffff\"/></svg>";
	held String is DEFAULT_CHECKBOX_OFF_SVG: "<svg viewBox=\"0 0 16 16\"><rect x=\"2.5\" y=\"2.5\" width=\"11\" height=\"11\" rx=\"2\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.5\"/></svg>";
	held String is DEFAULT_CHECKBOX_ON_SVG: "<svg viewBox=\"0 0 16 16\"><rect x=\"2.5\" y=\"2.5\" width=\"11\" height=\"11\" rx=\"2\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.5\"/><path d=\"M5 8.2L7.2 10.4L11.2 5.6\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>";

	Array of MenuConfig is menus: Array();
	Float is heightPt: 0.0;
	String is radioOffIconSvg: '';
	String is radioOnIconSvg: '';
	String is checkboxOffIconSvg: '';
	String is checkboxOnIconSvg: '';

	replace Function is init(
		Array of MenuConfig is menus: Array(),
		Float is heightPt: 0.0,
		String is radioOffIconSvg: '',
		String is radioOnIconSvg: '',
		String is checkboxOffIconSvg: '',
		String is checkboxOnIconSvg: ''
	){
		:menus: menus;
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
