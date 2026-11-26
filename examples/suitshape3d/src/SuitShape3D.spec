#! Package suitshape3d
#! Composition root for SuitShape3D (wires Model -> ViewModel -> View -> ToolkitContainer).

Class is SuitShape3D{
	replace [String] is namespace: ['suitshape3d'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Map],
		['base', 'cli', Cli],
		['base', 'scrap', ToolkitContainer],
		['suitshape3d', 'model', Shape3DModel],
		['suitshape3d', 'viewmodel', Shape3DViewModel],
		['suitshape3d', 'view', Shape3DView]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();
		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);

		local String is name: if({ cli:appName != '' }, { cli:appName }, { 'SuitShape3D' });
		local String is ver: if({ cli:appVersion != '' }, { cli:appVersion }, { '0.1.0' });
		local String is desc: if({ cli:appDescription != '' }, { cli:appDescription }, { 'Minimal Vulkan 3D spinning cube example' });

		local Shape3DModel is model: Shape3DModel(appName: name, version: ver, description: desc);
		local Shape3DViewModel is vm: Shape3DViewModel(model: model);
		local ToolkitContainer is app: Shape3DView():build(vm: vm);
		app:run(durationMs: durationMs);
	}
}
