#! Package base:theo
#! Overridable theme defining colors and border styles for Theo apps and widgets.

Class is TheoTheme{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', TheoColor]
	];

	TheoColor is foreground: TheoColor:ansi(code: 252);
	TheoColor is background: TheoColor:none();
	TheoColor is borderColor: TheoColor:ansi(code: 240);
	TheoColor is focusBorderColor: TheoColor:ansi(code: 255);
	Boolean is roundedBorders: true;
	TheoColor is titleColor: TheoColor:ansi(code: 255);
	TheoColor is mutedColor: TheoColor:ansi(code: 245);
	TheoColor is buttonFg: TheoColor:ansi(code: 252);
	TheoColor is buttonBg: TheoColor:ansi(code: 237);
	TheoColor is buttonFocusFg: TheoColor:ansi(code: 16);
	TheoColor is buttonFocusBg: TheoColor:ansi(code: 255);

	replace Function is init(
		TheoColor is foreground: TheoColor:ansi(code: 252),
		TheoColor is background: TheoColor:none(),
		TheoColor is borderColor: TheoColor:ansi(code: 240),
		TheoColor is focusBorderColor: TheoColor:ansi(code: 255),
		Boolean is roundedBorders: true,
		TheoColor is titleColor: TheoColor:ansi(code: 255),
		TheoColor is mutedColor: TheoColor:ansi(code: 245),
		TheoColor is buttonFg: TheoColor:ansi(code: 252),
		TheoColor is buttonBg: TheoColor:ansi(code: 237),
		TheoColor is buttonFocusFg: TheoColor:ansi(code: 16),
		TheoColor is buttonFocusBg: TheoColor:ansi(code: 255)
	){
		:foreground: foreground;
		:background: background;
		:borderColor: borderColor;
		:focusBorderColor: focusBorderColor;
		:roundedBorders: roundedBorders;
		:titleColor: titleColor;
		:mutedColor: mutedColor;
		:buttonFg: buttonFg;
		:buttonBg: buttonBg;
		:buttonFocusFg: buttonFocusFg;
		:buttonFocusBg: buttonFocusBg;
	}
}
