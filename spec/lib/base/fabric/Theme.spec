#! Package base:fabric
#! Theme tokens for Fabric 2D rendering and Scrap widgets.

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'suit', SuitCanvas]
	];

	Int is panelBg: 0;
	Int is panelBorder: 0;
	Int is textPrimary: 0;
	Int is textAccent: 0;
	Int is padding: 8;
	Int is fontScale: 2;

	replace Function is init(){
		local SuitCanvas is c: SuitCanvas(width: 1, height: 1);
		panelBg: c:argb(r: 18, g: 22, b: 32, a: 210);
		panelBorder: c:argb(r: 72, g: 88, b: 118, a: 235);
		textPrimary: c:argb(r: 242, g: 245, b: 250, a: 255);
		textAccent: c:argb(r: 100, g: 210, b: 255, a: 255);
		c:dispose();
	}
}
