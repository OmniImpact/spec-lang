#! Package specedit:viewmodel
#! Pure ViewModel for SpecEdit: exposes state, menu descriptors, and commands.
#! Zero imports from Suit, Sew, Fabric, or Scrap.

Class is EditorViewModel{
	replace [String] is namespace: ['specedit', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['specedit', 'model', EditorModel]
	];

	EditorModel is model: EditorModel();
	Boolean is running: true;
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 26.0;

	replace Function is init(EditorModel is model){
		:model: model;
		running: true;
	}

	Function of String is windowTitle(){
		if({ model:dirty }, {
			return 'SpecEdit - ' . model:documentName . ' *';
		});
		return 'SpecEdit - ' . model:documentName;
	}

	Function of Boolean is isRunning(){
		return running;
	}

	## Command invoked by the View when the user requests application exit.
	Function is requestQuit(){
		running: false;
	}

	## Pure menu descriptors: `[menuId, menuLabel, itemId, itemLabel]` tuples.
	Function of Array of String is fileMenuItemIds(){
		local Array of String is ids: Array();
		ids:add(item: 'quit');
		return ids;
	}

	Function of String is itemLabelForId(String is id){
		if({ id == 'quit' }, { return 'Quit'; });
		return id;
	}
}
