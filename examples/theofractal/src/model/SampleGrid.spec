#! Package theofractal:model
#! 2D sample buffer separating palette depth coordinate, edge AA coverage, and edge/depth glow.

Class is SampleGrid{
	replace [String] is namespace: ['theofractal', 'model'];

	[Float] is paletteT: [];
	[Float] is coverage: [];
	[Float] is edgeGlow: [];

	replace Function is init([Float] is paletteT: [], [Float] is coverage: [], [Float] is edgeGlow: []){
		:paletteT: paletteT;
		:coverage: coverage;
		:edgeGlow: edgeGlow;
	}

	Function of Int is length(){
		return paletteT:length();
	}
}
