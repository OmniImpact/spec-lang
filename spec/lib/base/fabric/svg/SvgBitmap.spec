#! Package base:fabric:svg
#! Cached rasterized SVG bitmap holding both alpha-coverage mask and pre-colored ARGB8888 buffer.

Class is SvgBitmap{
	replace [String] is namespace: ['base', 'fabric', 'svg'];

	replace [[String]] is using: [
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()]
	];

	Int is width: 0;
	Int is height: 0;
	Int is maskAddr: 0;
	Int is argbAddr: 0;

	replace Function is init(Int is width: 0, Int is height: 0, Int is maskAddr: 0, Int is argbAddr: 0){
		:width: width;
		:height: height;
		:maskAddr: maskAddr;
		:argbAddr: argbAddr;
	}

	Function is destroy(){
		if({ maskAddr != 0 }, { Mem:free(ptr: maskAddr); :maskAddr: 0; });
		if({ argbAddr != 0 }, { Mem:free(ptr: argbAddr); :argbAddr: 0; });
	}
}
