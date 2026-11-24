#! Package base:theo
#! Unboxed 32-bit packed RGB/RGBA color helpers (`0xAARRGGBB` stored in an `Int`).

Class is Color32{
	replace [String] is namespace: ['base', 'theo'];

	merge [[String]] is using: [
		['base', 'theo', TheoColor]
	];

	## Packs 8-bit RGB channels into an unboxed `0xFFRRGGBB` Int.
	held Function of Int is pack(Int is r, Int is g, Int is b){
		return (255 << 24) | ((r & 255) << 16) | ((g & 255) << 8) | (b & 255);
	}

	## Packs 8-bit RGBA channels into an unboxed `0xAARRGGBB` Int.
	held Function of Int is packRgba(Int is r, Int is g, Int is b, Int is a){
		return ((a & 255) << 24) | ((r & 255) << 16) | ((g & 255) << 8) | (b & 255);
	}

	## Extracts the 8-bit red channel (`0..255`).
	held Function of Int is red(Int is color){ (color >> 16) & 255 }

	## Extracts the 8-bit green channel (`0..255`).
	held Function of Int is green(Int is color){ (color >> 8) & 255 }

	## Extracts the 8-bit blue channel (`0..255`).
	held Function of Int is blue(Int is color){ color & 255 }

	## Extracts the 8-bit alpha channel (`0..255`).
	held Function of Int is alpha(Int is color){ (color >> 24) & 255 }

	## Averages 4 packed RGB colors (for 2x2 supersampled antialiasing) with zero heap allocation.
	held Function of Int is avg4(Int is c00, Int is c10, Int is c01, Int is c11){
		local Int is r: (((c00 >> 16) & 255) + ((c10 >> 16) & 255) + ((c01 >> 16) & 255) + ((c11 >> 16) & 255)) >> 2;
		local Int is g: (((c00 >> 8) & 255) + ((c10 >> 8) & 255) + ((c01 >> 8) & 255) + ((c11 >> 8) & 255)) >> 2;
		local Int is b: ((c00 & 255) + (c10 & 255) + (c01 & 255) + (c11 & 255)) >> 2;
		return (255 << 24) | (r << 16) | (g << 8) | b;
	}

	## Converts a packed 32-bit color to a [TheoColor].
	held Function of TheoColor is toTheoColor(Int is color){
		TheoColor:rgb(r: (color >> 16) & 255, g: (color >> 8) & 255, b: color & 255)
	}
}
