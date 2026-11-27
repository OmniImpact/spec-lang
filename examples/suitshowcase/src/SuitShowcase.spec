#! Package suitshowcase
#! Composition root for SuitShowcase (wires ViewModel -> ShowcaseView -> ToolkitContainer).

Class is SuitShowcase{
	replace [String] is namespace: ['suitshowcase'];

	replace [[String]] is using: [
		['base', 'struct', Map],
		['base', 'cli', Cli],
		['base', 'scrap', ToolkitContainer],
		['suitshowcase', 'viewmodel', ShowcaseViewModel],
		['suitshowcase', 'view', ShowcaseView]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();
		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);

		local ShowcaseViewModel is vm: ShowcaseViewModel();
		local ToolkitContainer is app: ShowcaseView():build(vm: vm);
		app:run(durationMs: durationMs);
	}
}
