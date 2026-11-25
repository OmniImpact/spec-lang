#! Package base:suit
#! TrueType/OpenType font renderer for SuitCanvas (backed by `stb_truetype`).

Class is SuitFont{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'suit', SuitCanvas],
		['base', 'sys', [as File(), Font]],
		['base', 'sys', as Conditional()]
	];

	Font is native: Font();

	## Loads a `.ttf`/`.otf` font from [path].
	Function of Boolean is load(String is path){
		return native:load(path: path);
	}

	## Attempts to load a standard system sans-serif or monospace TTF font.
	Function of Boolean is loadSystemFont(){
		local [String] is candidates: [
			'/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
			'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
			'/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
			'/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
			'/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
			'/System/Library/Fonts/Helvetica.ttc',
			'C:/Windows/Fonts/segoeui.ttf',
			'C:/Windows/Fonts/arial.ttf'
		];
		local Int is i: 0;
		while({ i < candidates:length() }, {
			local String is p: candidates:get(index: i);
			if({ fileExists(path: p) }, {
				if({ native:load(path: p) }, { return true; });
			});
			i: i + 1;
		});
		return false;
	}

	## Draws UTF-8 [text] onto [canvas] at ([x], [y]) with [size] px height and ARGB [color].
	Function of Boolean is drawText(SuitCanvas is canvas, Int is x, Int is y, String is text, Int is size: 16, Int is color: -1){
		return native:drawText(
			pixelsAddr: canvas:pixelsAddr(),
			bufW: canvas:width,
			bufH: canvas:height,
			x: x,
			y: y,
			text: text,
			pixelHeight: size,
			argbColor: color
		);
	}

	Function of Boolean is isLoaded(){
		return native:isLoaded();
	}

	Function is close(){
		native:close();
	}

	Function of String is lastError(){
		return native:lastError();
	}
}
