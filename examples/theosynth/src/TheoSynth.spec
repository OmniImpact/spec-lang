#! Package theosynth
#! Interactive 3-octave terminal synthesizer built with Spec, Theo, and base:audio.

Class is TheoSynth{
	replace [String] is namespace: ['theosynth'];

	merge [[String]] is using: [
		['base', 'theo', [TheoApp, TheoScreen]],
		['theosynth', 'vm', SynthViewModel],
		['theosynth', 'view', SynthFrame]
	];

	replace Function is init(){
		local TheoApp is app: TheoApp();
		local SynthViewModel is vm: SynthViewModel(onQuit: {
			app:quit();
		});
		local SynthFrame is frame: SynthFrame(vm: vm);
		local TheoScreen is screen: TheoScreen(root: frame);
		app:run(screen: screen);
	}
}
