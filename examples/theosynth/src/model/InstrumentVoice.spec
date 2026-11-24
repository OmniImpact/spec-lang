#! Package theosynth:model
#! Base per-note voice state managed by [SynthEngine] and rendered by an [Instrument].

Class is InstrumentVoice{
	replace [String] is namespace: ['theosynth', 'model'];

	Int is midi: 60;
	Int is gate: 1;
	Float is env: 0.0;
	Int is holdFrames: 660;
	Int is relPending: 0;
	Float is phase: 0.0;
	Float is step: 0.0;

	replace Function is init(Int is midi: 60, Float is step: 0.0, Float is initialEnv: 0.0){
		:midi: midi;
		:step: step;
		env: initialEnv;
		gate: 1;
		holdFrames: 660;
		relPending: 0;
		phase: 0.0;
	}

	## Renders one oscillator/waveguide sample in `[-1.0, 1.0]` and advances internal state.
	Function of Float is nextSample(){ 0.0 }

	## Releases any native buffers held by this voice.
	Function is destroy(){}
}
