#! Package base:fabric
#! Theme tokens for Fabric 2D rendering and Scrap widgets.

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'suit', SuitCanvas]
	];

	Int is windowBg: 0;
	Int is toolbarBg: 0;
	Int is tabBarBg: 0;
	Int is toolbarBorder: 0;
	Int is menuBg: 0;
	Int is menuBorder: 0;
	Int is hoverBg: 0;
	Int is activeBg: 0;
	Int is panelBg: 0;
	Int is panelBorder: 0;
	Int is textPrimary: 0;
	Int is textMuted: 0;
	Int is textAccent: 0;
	Float is toolbarHeightPt: 30.0;
	Float is menuItemHeightPt: 28.0;
	Float is paddingPt: 8.0;

	replace Function is init(String is preset: 'dark'){
		local SuitCanvas is c: SuitCanvas(width: 1, height: 1);
		if({ preset == 'light_grayscale' }, {
			windowBg: c:argb(r: 255, g: 255, b: 255, a: 255);
			toolbarBg: c:argb(r: 230, g: 230, b: 230, a: 255);
			tabBarBg: c:argb(r: 214, g: 214, b: 214, a: 255);
			toolbarBorder: c:argb(r: 196, g: 196, b: 196, a: 255);
			menuBg: c:argb(r: 245, g: 245, b: 245, a: 255);
			menuBorder: c:argb(r: 178, g: 178, b: 178, a: 255);
			hoverBg: c:argb(r: 210, g: 210, b: 210, a: 255);
			activeBg: c:argb(r: 190, g: 190, b: 190, a: 255);
			panelBg: c:argb(r: 242, g: 242, b: 242, a: 255);
			panelBorder: c:argb(r: 196, g: 196, b: 196, a: 255);
			textPrimary: c:argb(r: 28, g: 28, b: 28, a: 255);
			textMuted: c:argb(r: 96, g: 96, b: 96, a: 255);
			textAccent: c:argb(r: 40, g: 40, b: 40, a: 255);
		}, {
			windowBg: c:argb(r: 20, g: 23, b: 33, a: 255);
			toolbarBg: c:argb(r: 32, g: 37, b: 50, a: 255);
			tabBarBg: c:argb(r: 24, g: 28, b: 38, a: 255);
			toolbarBorder: c:argb(r: 64, g: 76, b: 102, a: 255);
			menuBg: c:argb(r: 36, g: 42, b: 56, a: 255);
			menuBorder: c:argb(r: 72, g: 88, b: 118, a: 255);
			hoverBg: c:argb(r: 54, g: 64, b: 86, a: 255);
			activeBg: c:argb(r: 68, g: 82, b: 110, a: 255);
			panelBg: c:argb(r: 18, g: 22, b: 32, a: 210);
			panelBorder: c:argb(r: 72, g: 88, b: 118, a: 235);
			textPrimary: c:argb(r: 242, g: 245, b: 250, a: 255);
			textMuted: c:argb(r: 160, g: 170, b: 190, a: 255);
			textAccent: c:argb(r: 100, g: 210, b: 255, a: 255);
		});
		c:dispose();
	}
}
