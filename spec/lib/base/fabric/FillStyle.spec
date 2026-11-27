#! Package base:fabric
#! Composable fill and color-effect style supporting solid, linear, and radial gradients (with centerpoint, blend width, reflected mode) plus brightness, tint, and saturation shifts.

Class is FillStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', as Math()],
		['base', 'fabric', Color]
	];

	String is mode: 'solid';
	Color is colorA: Color(r: 40, g: 44, b: 56);
	Color is colorB: Color(r: 90, g: 150, b: 235);
	Float is centerX: 0.5;
	Float is centerY: 0.5;
	Float is angleDeg: 0.0;
	Float is blendWidth: 1.0;
	Boolean is reflected: false;
	Float is brightness: 0.0;
	Float is tintShiftDeg: 0.0;
	Float is saturationShift: 0.0;

	replace Function is init(
		String is mode: 'solid',
		Color is colorA: Color(r: 40, g: 44, b: 56),
		Color is colorB: Color(r: 90, g: 150, b: 235),
		Float is centerX: 0.5,
		Float is centerY: 0.5,
		Float is angleDeg: 0.0,
		Float is blendWidth: 1.0,
		Boolean is reflected: false,
		Float is brightness: 0.0,
		Float is tintShiftDeg: 0.0,
		Float is saturationShift: 0.0
	){
		:mode: mode;
		:colorA: colorA;
		:colorB: colorB;
		:centerX: Color:clamp01(v: centerX);
		:centerY: Color:clamp01(v: centerY);
		:angleDeg: angleDeg;
		:blendWidth: if({ blendWidth < 0.05 }, { 0.05 }, { blendWidth });
		:reflected: reflected;
		:brightness: brightness;
		:tintShiftDeg: tintShiftDeg;
		:saturationShift: saturationShift;
	}

	Function of Boolean is isSolid(){
		return mode == 'solid';
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
		if({ mode == 'solid' }, {
			return :applyEffects(c: colorA);
		});
		local Float is bw: if({ blendWidth < 0.05 }, { 0.05 }, { blendWidth });
		local Float is t: 0.0;
		if({ mode == 'radial' }, {
			local Float is dx: u - centerX;
			local Float is dy: v - centerY;
			local Float is dist: sqrt(value: dx * dx + dy * dy);
			local Float is rMax: bw * 0.5;
			if({ rMax < 0.05 }, { rMax: 0.05; });
			if({ reflected }, {
				t: Color:clamp01(v: 1.0 - dist / rMax);
			}, {
				t: Color:clamp01(v: dist / rMax);
			});
		}, {
			local Float is rad: (angleDeg * pi()) / 180.0;
			local Float is ux: cos(value: rad);
			local Float is uy: sin(value: rad);
			local Float is proj: (u - centerX) * ux + (v - centerY) * uy;
			if({ reflected }, {
				local Float is absP: if({ proj < 0.0 }, { 0.0 - proj }, { proj });
				t: Color:clamp01(v: 1.0 - absP / (bw * 0.5));
			}, {
				t: Color:clamp01(v: 0.5 + proj / bw);
			});
		});
		return :applyEffects(c: colorA:mix(other: colorB, t: t));
	}
}
