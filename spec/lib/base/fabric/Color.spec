#! Package base:fabric
#! ARGB8888 color value and manipulation library (lighten, darken, mix, tint, hue rotation, alpha).

Class is Color{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Conditional],
		['base', 'sys', Loops]
	];

	Int is argb: -16777216;

	replace Function is init(Int is r: 0, Int is g: 0, Int is b: 0, Int is a: 255){
		local Int is ca: Color:clampByte(v: a);
		local Int is cr: Color:clampByte(v: r);
		local Int is cg: Color:clampByte(v: g);
		local Int is cb: Color:clampByte(v: b);
		:argb: (ca << 24) | (cr << 16) | (cg << 8) | cb;
	}

	held Function of Int is clampByte(Int is v){
		return Conditional:if(check: { v < 0 }, then: { 0 }, else: {
			Conditional:if(check: { v > 255 }, then: { 255 }, else: { v })
		});
	}

	held Function of Float is clamp01(Float is v){
		return Conditional:if(check: { v < 0.0 }, then: { 0.0 }, else: {
			Conditional:if(check: { v > 1.0 }, then: { 1.0 }, else: { v })
		});
	}

	held Function of Color is fromArgb(Int is argb){
		local Color is c: Color();
		c:argb: argb;
		return c;
	}

	held Function of Color is rgba(Int is r, Int is g, Int is b, Float is a: 1.0){
		local Int is ab: ((Color:clamp01(v: a) * 255.0) + 0.5) as Int;
		return Color(r: r, g: g, b: b, a: ab);
	}

	Function of Int is alpha(){ return (argb >> 24) & 255; }
	Function of Int is red(){ return (argb >> 16) & 255; }
	Function of Int is green(){ return (argb >> 8) & 255; }
	Function of Int is blue(){ return argb & 255; }
	Function of Int is toArgb(){ return argb; }

	Function of Float is alphaF(){
		return (:alpha() as Float) / 255.0;
	}

	Function of Color is withAlphaByte(Int is a){
		local Int is ca: Color:clampByte(v: a);
		return Color:fromArgb(argb: (ca << 24) | (argb & 16777215));
	}

	Function of Color is withAlpha(Float is a){
		local Int is ab: ((Color:clamp01(v: a) * 255.0) + 0.5) as Int;
		return :withAlphaByte(a: ab);
	}

	Function of Float is luminance(){
		local Float is r: (:red() as Float) / 255.0;
		local Float is g: (:green() as Float) / 255.0;
		local Float is b: (:blue() as Float) / 255.0;
		return 0.2126 * r + 0.7152 * g + 0.0722 * b;
	}

	Function of Boolean is isLight(){
		return :luminance() >= 0.5;
	}

	Function of Color is mix(Color is other, Float is t){
		local Float is k: Color:clamp01(v: t);
		local Float is inv: 1.0 - k;
		local Int is r: (((:red() as Float) * inv + (other:red() as Float) * k) + 0.5) as Int;
		local Int is g: (((:green() as Float) * inv + (other:green() as Float) * k) + 0.5) as Int;
		local Int is b: (((:blue() as Float) * inv + (other:blue() as Float) * k) + 0.5) as Int;
		local Int is a: (((:alpha() as Float) * inv + (other:alpha() as Float) * k) + 0.5) as Int;
		return Color(r: r, g: g, b: b, a: a);
	}

	Function of Color is tint(Color is target, Float is amount){
		local Color is blended: :mix(other: target, t: amount);
		return blended:withAlphaByte(a: :alpha());
	}

	Function of Color is lighten(Float is amount){
		return :tint(target: Color(r: 255, g: 255, b: 255, a: :alpha()), amount: amount);
	}

	Function of Color is darken(Float is amount){
		return :tint(target: Color(r: 0, g: 0, b: 0, a: :alpha()), amount: amount);
	}

	Function of Color is rotateHue(Float is degrees){
		local Float is r: (:red() as Float) / 255.0;
		local Float is g: (:green() as Float) / 255.0;
		local Float is b: (:blue() as Float) / 255.0;
		local Float is maxC: r;
		if({ g > maxC }, { maxC: g; });
		if({ b > maxC }, { maxC: b; });
		local Float is minC: r;
		if({ g < minC }, { minC: g; });
		if({ b < minC }, { minC: b; });
		local Float is l: (maxC + minC) * 0.5;
		local Float is d: maxC - minC;
		if({ d <= 0.00001 }, {
			return Color:fromArgb(argb: argb);
		});
		local Float is s: if({ l > 0.5 }, { d / (2.0 - maxC - minC) }, { d / (maxC + minC) });
		local Float is h: 0.0;
		if({ maxC == r }, {
			h: ((g - b) / d) + (if({ g < b }, { 6.0 }, { 0.0 }));
		}, {
			if({ maxC == g }, {
				h: ((b - r) / d) + 2.0;
			}, {
				h: ((r - g) / d) + 4.0;
			});
		});
		h: h / 6.0;
		local Float is shift: degrees / 360.0;
		h: h + shift;
		while({ h < 0.0 }, { h: h + 1.0; });
		while({ h >= 1.0 }, { h: h - 1.0; });

		local Float is q: if({ l < 0.5 }, { l * (1.0 + s) }, { l + s - l * s });
		local Float is p: 2.0 * l - q;
		local Int is nr: ((Color:hslChan(p: p, q: q, tRaw: h + (1.0 / 3.0)) * 255.0) + 0.5) as Int;
		local Int is ng: ((Color:hslChan(p: p, q: q, tRaw: h) * 255.0) + 0.5) as Int;
		local Int is nb: ((Color:hslChan(p: p, q: q, tRaw: h - (1.0 / 3.0)) * 255.0) + 0.5) as Int;
		return Color(r: nr, g: ng, b: nb, a: :alpha());
	}

	Function of Color is saturate(Float is amount){
		local Float is k: Color:clamp01(v: amount);
		local Int is avg: (:red() + :green() + :blue()) / 3;
		local Int is r: Color:clampByte(v: :red() + ((((:red() - avg) as Float) * k) as Int));
		local Int is g: Color:clampByte(v: :green() + ((((:green() - avg) as Float) * k) as Int));
		local Int is b: Color:clampByte(v: :blue() + ((((:blue() - avg) as Float) * k) as Int));
		return Color(r: r, g: g, b: b, a: :alpha());
	}

	held Function of Float is hslChan(Float is p, Float is q, Float is tRaw){
		local Float is t: tRaw;
		Conditional:if(check: { t < 0.0 }, then: { t: t + 1.0; });
		Conditional:if(check: { t > 1.0 }, then: { t: t - 1.0; });
		Conditional:if(check: { t < (1.0 / 6.0) }, then: { return p + (q - p) * 6.0 * t; });
		Conditional:if(check: { t < 0.5 }, then: { return q; });
		Conditional:if(check: { t < (2.0 / 3.0) }, then: { return p + (q - p) * ((2.0 / 3.0) - t) * 6.0; });
		return p;
	}

	held Function of Color is fromHsl(Float is hDeg, Float is s, Float is l, Int is a: 255){
		local Float is hh: hDeg / 360.0;
		Loops:while(check: { hh < 0.0 }, body: { hh: hh + 1.0; });
		Loops:while(check: { hh >= 1.0 }, body: { hh: hh - 1.0; });
		local Float is cs: Color:clamp01(v: s);
		local Float is cl: Color:clamp01(v: l);
		Conditional:if(check: { cs <= 0.00001 }, then: {
			local Int is gv: ((cl * 255.0) + 0.5) as Int;
			return Color(r: gv, g: gv, b: gv, a: a);
		});
		local Float is q: Conditional:if(check: { cl < 0.5 }, then: { cl * (1.0 + cs) }, else: { cl + cs - cl * cs });
		local Float is p: 2.0 * cl - q;
		local Int is nr: ((Color:hslChan(p: p, q: q, tRaw: hh + (1.0 / 3.0)) * 255.0) + 0.5) as Int;
		local Int is ng: ((Color:hslChan(p: p, q: q, tRaw: hh) * 255.0) + 0.5) as Int;
		local Int is nb: ((Color:hslChan(p: p, q: q, tRaw: hh - (1.0 / 3.0)) * 255.0) + 0.5) as Int;
		return Color(r: nr, g: ng, b: nb, a: a);
	}

	Function of Float is hueDeg(){
		local Float is r: (:red() as Float) / 255.0;
		local Float is g: (:green() as Float) / 255.0;
		local Float is b: (:blue() as Float) / 255.0;
		local Float is maxC: r;
		if({ g > maxC }, { maxC: g; });
		if({ b > maxC }, { maxC: b; });
		local Float is minC: r;
		if({ g < minC }, { minC: g; });
		if({ b < minC }, { minC: b; });
		local Float is d: maxC - minC;
		if({ d <= 0.00001 }, { return 0.0; });
		local Float is h: 0.0;
		if({ maxC == r }, {
			h: ((g - b) / d) + (if({ g < b }, { 6.0 }, { 0.0 }));
		}, {
			if({ maxC == g }, {
				h: ((b - r) / d) + 2.0;
			}, {
				h: ((r - g) / d) + 4.0;
			});
		});
		return h * 60.0;
	}

	Function of Float is saturation(){
		local Float is r: (:red() as Float) / 255.0;
		local Float is g: (:green() as Float) / 255.0;
		local Float is b: (:blue() as Float) / 255.0;
		local Float is maxC: r;
		if({ g > maxC }, { maxC: g; });
		if({ b > maxC }, { maxC: b; });
		local Float is minC: r;
		if({ g < minC }, { minC: g; });
		if({ b < minC }, { minC: b; });
		local Float is d: maxC - minC;
		if({ d <= 0.00001 }, { return 0.0; });
		local Float is l: (maxC + minC) * 0.5;
		return if({ l > 0.5 }, { d / (2.0 - maxC - minC) }, { d / (maxC + minC) });
	}

	Function of Float is lightness(){
		local Float is r: (:red() as Float) / 255.0;
		local Float is g: (:green() as Float) / 255.0;
		local Float is b: (:blue() as Float) / 255.0;
		local Float is maxC: r;
		if({ g > maxC }, { maxC: g; });
		if({ b > maxC }, { maxC: b; });
		local Float is minC: r;
		if({ g < minC }, { minC: g; });
		if({ b < minC }, { minC: b; });
		return (maxC + minC) * 0.5;
	}

	local Function of String is byteHex(Int is v){
		local String is digits: '0123456789ABCDEF';
		local Int is hi: (v >> 4) & 15;
		local Int is lo: v & 15;
		return digits:substring(start: hi, end: hi + 1) . digits:substring(start: lo, end: lo + 1);
	}

	Function of String is toHex(){
		return '#' . :byteHex(v: :red()) . :byteHex(v: :green()) . :byteHex(v: :blue());
	}

	Function of String is toHexAlpha(){
		return :toHex() . :byteHex(v: :alpha());
	}

	held Function of Int is hexVal(Int is b){
		Conditional:if(check: { b >= 48 && b <= 57 }, then: { return b - 48; });
		Conditional:if(check: { b >= 65 && b <= 70 }, then: { return 10 + (b - 65); });
		Conditional:if(check: { b >= 97 && b <= 102 }, then: { return 10 + (b - 97); });
		return -1;
	}

	held Function of Color is fromHex(String is hex, Color is fallback){
		local String is t: hex:trim();
		Conditional:if(check: { t:length() > 0 && t:byteAt(index: 0) == 35 }, then: {
			t: t:substring(start: 1, end: t:length());
		});
		Conditional:if(check: { t:length() != 6 }, then: { return fallback; });
		local Int is r1: Color:hexVal(b: t:byteAt(index: 0));
		local Int is r2: Color:hexVal(b: t:byteAt(index: 1));
		local Int is g1: Color:hexVal(b: t:byteAt(index: 2));
		local Int is g2: Color:hexVal(b: t:byteAt(index: 3));
		local Int is b1: Color:hexVal(b: t:byteAt(index: 4));
		local Int is b2: Color:hexVal(b: t:byteAt(index: 5));
		Conditional:if(check: { r1 < 0 || r2 < 0 || g1 < 0 || g2 < 0 || b1 < 0 || b2 < 0 }, then: { return fallback; });
		return Color(r: (r1 << 4) | r2, g: (g1 << 4) | g2, b: (b1 << 4) | b2);
	}
}
