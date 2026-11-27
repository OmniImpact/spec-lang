#! Package base:fabric
#! Bounds fitting mode for gradient fills: INSCRIBE (clamps inside edges/unit span) or CIRCUMSCRIBE (reaches furthest corner).

Enum is GradientBounds{
	replace [String] is namespace: ['base', 'fabric'];

	INSCRIBE,
	CIRCUMSCRIBE
}
