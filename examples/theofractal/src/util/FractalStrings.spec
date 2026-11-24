#! Package theofractal:util
#! Shared UI labels, fractal/theme names, and Help dialog copy for TheoFractal.

Class is FractalStrings{
	replace [String] is namespace: ['theofractal', 'util'];

	held String is ACTION_QUIT: ' Quit ';
	held String is ACTION_HELP: ' Help ';
	held String is ACTION_CLOSE: ' Close ';
	held String is LABEL_THEME: 'Theme:';

	held String is OPT_SELECT_FRACTAL: 'Select Fractal';
	held String is OPT_SIERPINSKI: 'Sierpinski';
	held String is OPT_SNOWFLAKE: 'Snowflake';
	held String is OPT_MANDELBROT: 'Mandelbrot';
	held String is OPT_BARNSLEY_FERN: 'Barnsley Fern';
	held String is OPT_JULIA: 'Julia Set';
	held String is OPT_BURNING_SHIP: 'Burning Ship';
	held String is OPT_DRAGON: 'Dragon Curve';

	held String is THEME_GRAYSCALE: 'Grayscale';
	held String is THEME_COOL: 'Cool';
	held String is THEME_WARM: 'Warm';
	held String is THEME_RAINBOW: 'Rainbow';

	held String is NAV_UP: ' ▲ ';
	held String is NAV_DOWN: ' ▼ ';
	held String is NAV_LEFT: ' ◀ ';
	held String is NAV_RIGHT: ' ▶ ';
	held String is NAV_ZOOM_IN: ' + ';
	held String is NAV_ZOOM_OUT: ' - ';

	held String is HELP_TITLE: ' TheoFractal Help ';
	held String is HELP_ABOUT_HDR: 'About TheoFractal';
	held String is HELP_ABOUT_1: 'Interactive terminal fractal explorer built with Spec & Theo.';
	held String is HELP_ABOUT_2: 'Fractals: Sierpinski, Snowflake, Mandelbrot, Barnsley Fern,';
	held String is HELP_ABOUT_3: '          Julia Set, Burning Ship, and Dragon Curve.';
	held String is HELP_ABOUT_4: 'Themes:   Grayscale, Cool, Warm, Rainbow.';
	held String is HELP_KEYS_HDR: 'Keyboard Shortcuts';
	held String is HELP_KEY_PAN: 'W / A / S / D   Pan Up / Left / Down / Right';
	held String is HELP_KEY_ZOOM: 'E / Q           Zoom In / Zoom Out';
	held String is HELP_KEY_RESET: 'R               Reset Camera View';
	held String is HELP_KEY_HELP: 'H or ?          Open This Help Dialog';
	held String is HELP_KEY_NAV: 'Tab / Esc       Cycle Focus / Close Dialog or Menu';

	held Function of [String] is fractalOptions(){
		[
			FractalStrings:OPT_SELECT_FRACTAL,
			FractalStrings:OPT_SIERPINSKI,
			FractalStrings:OPT_SNOWFLAKE,
			FractalStrings:OPT_MANDELBROT,
			FractalStrings:OPT_BARNSLEY_FERN,
			FractalStrings:OPT_JULIA,
			FractalStrings:OPT_BURNING_SHIP,
			FractalStrings:OPT_DRAGON
		]
	}

	held Function of [String] is themeOptions(){
		[
			FractalStrings:THEME_GRAYSCALE,
			FractalStrings:THEME_COOL,
			FractalStrings:THEME_WARM,
			FractalStrings:THEME_RAINBOW
		]
	}
}
