#! Package base:cleo
#! Character glyph sets for Cleo outer borders and inner dividers.

Class is BorderGlyphs{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'cleo', BorderStyle],
		['base', 'sys', as Conditional()]
	];

	String is topLeft: '';
	String is top: '';
	String is topRight: '';
	String is left: '';
	String is right: '';
	String is bottomLeft: '';
	String is bottom: '';
	String is bottomRight: '';
	String is divLeft: '';
	String is divMid: '';
	String is divRight: '';

	replace Function is init(){
	}

	Function of BorderGlyphs is forStyle(BorderStyle is style){
		local BorderGlyphs is g: BorderGlyphs:init();
		if({ style == BorderStyle:ASCII }, {
			g:topLeft: '+';  g:top: '-';  g:topRight: '+';
			g:left: '|';                  g:right: '|';
			g:bottomLeft: '+'; g:bottom: '-'; g:bottomRight: '+';
			g:divLeft: '+';  g:divMid: '-'; g:divRight: '+';
			return g;
		});
		if({ style == BorderStyle:THIN }, {
			g:topLeft: '┌';  g:top: '─';  g:topRight: '┐';
			g:left: '│';                  g:right: '│';
			g:bottomLeft: '└'; g:bottom: '─'; g:bottomRight: '┘';
			g:divLeft: '├';  g:divMid: '─'; g:divRight: '┤';
			return g;
		});
		if({ style == BorderStyle:THICK }, {
			g:topLeft: '┏';  g:top: '━';  g:topRight: '┓';
			g:left: '┃';                  g:right: '┃';
			g:bottomLeft: '┗'; g:bottom: '━'; g:bottomRight: '┛';
			g:divLeft: '┣';  g:divMid: '━'; g:divRight: '┫';
			return g;
		});
		if({ style == BorderStyle:DOUBLE }, {
			g:topLeft: '╔';  g:top: '═';  g:topRight: '╗';
			g:left: '║';                  g:right: '║';
			g:bottomLeft: '╚'; g:bottom: '═'; g:bottomRight: '╝';
			g:divLeft: '╠';  g:divMid: '═'; g:divRight: '╣';
			return g;
		});
		if({ style == BorderStyle:ROUNDED }, {
			g:topLeft: '╭';  g:top: '─';  g:topRight: '╮';
			g:left: '│';                  g:right: '│';
			g:bottomLeft: '╰'; g:bottom: '─'; g:bottomRight: '╯';
			g:divLeft: '├';  g:divMid: '─'; g:divRight: '┤';
			return g;
		});
		if({ style == BorderStyle:DASHED }, {
			g:topLeft: '┌';  g:top: '╌';  g:topRight: '┐';
			g:left: '┆';                  g:right: '┆';
			g:bottomLeft: '└'; g:bottom: '╌'; g:bottomRight: '┘';
			g:divLeft: '├';  g:divMid: '╌'; g:divRight: '┤';
			return g;
		});
		return g;
	}
}
