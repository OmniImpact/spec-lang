#! Entry point for the Theo simple text editor example.

Class of TheoApp is EditorApp{
	replace Array of Array of String is using: [
		['base', 'theo', TheoApp],
		['base', 'theo', TheoScreen],
		['base', 'theo', TheoTheme],
		['base', 'struct', Map],
		[EditorViewModel],
		[EditorFrame]
	];

	replace Function is init(Map of String to String is args){
		local String is filePath: args:getString(key: '0', default: '');
		local TheoTheme is appTheme: TheoTheme();
		local EditorViewModel is vm: EditorViewModel(filePath: filePath);
		local EditorFrame is rootFrame: EditorFrame(
			vm: vm,
			theme: appTheme,
			onQuit: {
				quit();
			}
		);
		local TheoScreen is screen: TheoScreen(root: rootFrame);
		rootFrame:bindScreen(screen: screen);
		:run(screen: screen);
	}
}
