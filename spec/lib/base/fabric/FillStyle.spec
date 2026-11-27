#! Package base:fabric
#! Composable fill and color-effect style supporting solid, linear, and radial gradients (with centerpoint, blend width, reflected mode) plus brightness, tint, and saturation shifts.

Class is FillStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', as Math()],
		['base', 'fabric', Color],
		['base', 'fabric', FillMode],
		['base', 'fabric', GradientBounds]
	];

	FillMode is mode: FillMode:SOLID;
	GradientBounds is bounds: GradientBounds:INSCRIBE;
	Color is colorA: Color(r: 40, g: 44, b: 56);
	Color is colorB: Color(r: 90, g: 150, b: 235);
	Float is centerX: 0.5;
	Float is centerY: 0.5;
	Float is angleDeg: 0.0;
	Float is blendWidth: 0.5;
	Boolean is reflected: false;
	Float is brightness: 0.0;
	Float is tintShiftDeg: 0.0;
	Float is saturationShift: 0.0;

	replace Function is init(
		FillMode is mode: FillMode:SOLID,
		GradientBounds is bounds: GradientBounds:INSCRIBE,
		Color is colorA: Color(r: 40, g: 44, b: 56),
		Color is colorB: Color(r: 90, g: 150, b: 235),
		Float is centerX: 0.5,
		Float is centerY: 0.5,
		Float is angleDeg: 0.0,
		Float is blendWidth: 0.5,
		Boolean is reflected: false,
		Float is brightness: 0.0,
		Float is tintShiftDeg: 0.0,
		Float is saturationShift: 0.0
	){
		:mode: mode;
		:bounds: bounds;
		:colorA: colorA;
		:colorB: colorB;
		:centerX: Color:clamp01(v: centerX);
		:centerY: Color:clamp01(v: centerY);
		:angleDeg: angleDeg;
		:blendWidth: Color:clamp01(v: blendWidth);
		:reflected: reflected;
		:brightness: brightness;
		:tintShiftDeg: tintShiftDeg;
		:saturationShift: saturationShift;
	}

	Function of Boolean is isSolid(){
		return mode == FillMode:SOLID;
	}

	## Applies tint (hue) shift, saturation shift, and brightness modulation to [c].
	Function of Color is applyEffects(Color is c){
		local Color is out: c;
		if({ tintShiftDeg != 0.0 }, {
			out: out:rotateHue(degrees: tintShiftDeg);
		});
		if({ saturationShift != 0.0 }, {
			out: out:saturate(amount: saturationShift);
		});
		if({ brightness > 0.0 }, {
			local Float is amt: if({ brightness > 1.0 }, { 1.0 }, { brightness });
			out: out:lighten(amount: amt);
		}, {
		if({ brightness < 0.0 }, {
			local Float is amt: if({ brightness < -1.0 }, { 1.0 }, { 0.0 - brightness });
			out: out:darken(amount: amt);
		}); });
		return out;
	}

	## Samples the fill at normalized coordinates ([u], [v]) in [0, 1] x [0, 1].
	Function of Color is sampleAt(Float is u, Float is v){
		if({ mode == FillMode:SOLID }, {
			return :applyEffects(c: colorA);
		});
		local Float is b: Color:clamp01(v: blendWidth);
		local Float is t: 0.0;
		if({ mode == FillMode:RADIAL }, {
			local Float is dx: u - centerX;
			local Float is dy: v - centerY;
			local Float is radMaxD: 0.5;
			if({ bounds == GradientBounds:CIRCUMSCRIBE }, {
				local Float is mx: if({ centerX > 1.0 - centerX }, { centerX }, { 1.0 - centerX });
				local Float is my: if({ centerY > 1.0 - centerY }, { centerY }, { 1.0 - centerY });
				radMaxD: sqrt(value: mx * mx + my * my);
				if({ radMaxD < 0.001 }, { radMaxD: 0.001; });
			});
			local Float is dist: sqrt(value: dx * dx + dy * dy) / radMaxD;
			if({ b <= 0.001 }, {
				t: if({ dist <= 0.001 }, { 0.0 }, { 1.0 });
			}, {
			if({ b >= 0.999 }, {
				t: 0.0;
			}, {
				local Float is lo: if({ b > 0.5 }, { (b - 0.5) * 2.0 }, { 0.0 });
				local Float is hi: if({ b > 0.5 }, { 1.0 }, { b * 2.0 });
				local Float is span: if({ hi - lo < 0.001 }, { 0.001 }, { hi - lo });
				t: Color:clamp01(v: (dist - lo) / span);
			}); });
			if({ reflected }, { t: 1.0 - t; });
		}, {
			local Float is rad: (angleDeg * pi()) / 180.0;
			local Float is ux: cos(value: rad);
			local Float is uy: sin(value: rad);
			local Float is proj: (u - centerX) * ux + (v - centerY) * uy;
			local Float is halfSpan: 0.5;
			if({ bounds == GradientBounds:CIRCUMSCRIBE }, {
				local Float is p00: (0.0 - centerX) * ux + (0.0 - centerY) * uy;
				local Float is p10: (1.0 - centerX) * ux + (0.0 - centerY) * uy;
				local Float is p01: (0.0 - centerX) * ux + (1.0 - centerY) * uy;
				local Float is p11: (1.0 - centerX) * ux + (1.0 - centerY) * uy;
				local Float is a00: if({ p00 < 0.0 }, { 0.0 - p00 }, { p00 });
				local Float is a10: if({ p10 < 0.0 }, { 0.0 - p10 }, { p10 });
				local Float is a01: if({ p01 < 0.0 }, { 0.0 - p01 }, { p01 });
				local Float is a11: if({ p11 < 0.0 }, { 0.0 - p11 }, { p11 });
				halfSpan: a00;
				if({ a10 > halfSpan }, { halfSpan: a10; });
				if({ a01 > halfSpan }, { halfSpan: a01; });
				if({ a11 > halfSpan }, { halfSpan: a11; });
				if({ halfSpan < 0.001 }, { halfSpan: 0.001; });
			});
			if({ reflected }, {
				local Float is absP: if({ proj < 0.0 }, { 0.0 - proj }, { proj });
				local Float is dist: absP / halfSpan;
				if({ b <= 0.001 }, {
					t: if({ dist <= 0.01 }, { 1.0 }, { 0.0 });
				}, {
				if({ b >= 0.999 }, {
					t: 1.0;
				}, {
					local Float is lo: if({ b > 0.5 }, { (b - 0.5) * 2.0 }, { 0.0 });
					local Float is hi: if({ b > 0.5 }, { 1.0 }, { b * 2.0 });
					local Float is span: if({ hi - lo < 0.001 }, { 0.001 }, { hi - lo });
					t: 1.0 - Color:clamp01(v: (dist - lo) / span);
				}); });
			}, {
				local Float is pos: 0.5 + proj / (2.0 * halfSpan);
				if({ b <= 0.001 }, {
					t: if({ pos >= 0.5 }, { 1.0 }, { 0.0 });
				}, {
				if({ b >= 0.999 }, {
					t: 0.5;
				}, {
				if({ b > 0.5 }, {
					local Float is edge: 1.0 - b;
					if({ pos <= edge }, {
						t: Color:clamp01(v: pos / edge) * 0.5;
					}, {
					if({ pos >= b }, {
						t: 0.5 + Color:clamp01(v: (pos - b) / edge) * 0.5;
					}, {
						t: 0.5;
					}); });
				}, {
					local Float is lo: 0.5 - b;
					local Float is hi: 0.5 + b;
					local Float is span: if({ hi - lo < 0.001 }, { 0.001 }, { hi - lo });
					t: Color:clamp01(v: (pos - lo) / span);
				}); }); });
			});
		});
		return :applyEffects(c: colorA:mix(other: colorB, t: t));
	}
}
