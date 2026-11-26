#! Package base:fabric
#! ARGB8888 color value and manipulation library (lighten, darken, mix, tint, hue rotation, alpha).

Class is Color{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
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

	local Function of Float is hueToRgb(Float is p, Float is q, Float is tRaw){
		local Float is t: tRaw;
		if({ t < 0.0 }, { t: t + 1.0; });
		if({ t > 1.0 }, { t: t - 1.0; });
		if({ t < (1.0 / 6.0) }, { return p + (q - p) * 6.0 * t; });
		if({ t < 0.5 }, { return q; });
		if({ t < (2.0 / 3.0) }, { return p + (q - p) * ((2.0 / 3.0) - t) * 6.0; });
		return p;
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
		local Int is nr: ((:hueToRgb(p: p, q: q, tRaw: h + (1.0 / 3.0)) * 255.0) + 0.5) as Int;
		local Int is ng: ((:hueToRgb(p: p, q: q, tRaw: h) * 255.0) + 0.5) as Int;
		local Int is nb: ((:hueToRgb(p: p, q: q, tRaw: h - (1.0 / 3.0)) * 255.0) + 0.5) as Int;
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
}
