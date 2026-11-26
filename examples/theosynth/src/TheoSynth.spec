#! Package theosynth
#! Interactive 3-octave terminal synthesizer built with Spec, Theo, and base:audio.

Class is TheoSynth{
	replace [String] is namespace: ['theosynth'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'core', SpecError],
		['base', 'sys', [as Conditional(), as Process()]],
		['base', 'sys', 'thread', ThreadScope],
		['theosynth', 'vm', SynthViewModel],
		['theosynth', 'view', SynthFrame]
	];

	replace Function is init(){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/theosynth/cli.json');
		if({ !cli:parse(rawArgs: rawArgs()) }, {
			if({ cli:helpRequested || cli:versionRequested }, { return; });
			exit(status: 1);
		});
		local TheoApp is app: TheoApp();
		local SynthViewModel is vm: SynthViewModel(onQuit: {
			app:quit();
		});
		local SynthFrame is frame: SynthFrame(vm: vm);
		local TheoScreen is screen: TheoScreen(root: frame);
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				vm:startAudio(scope: scope);
				app:run(screen: screen);
				vm:engine:close();
			},
			onError: local Function of Boolean(SpecError is _err){ false }
		);
	}
}
