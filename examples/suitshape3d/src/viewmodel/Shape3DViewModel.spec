#! Package suitshape3d:viewmodel
#! Pure MVVM ViewModel for SuitShape3D: owns reactive Emitters, ToolbarConfig, FPS tracking, and MVP math.

Class is Shape3DViewModel{
	replace [String] is namespace: ['suitshape3d', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', Math],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'scrap', ToolbarConfig],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', MenuItemConfig],
		['base', 'mold', Mat4],
		['suitshape3d', 'model', Shape3DModel]
	];

	Shape3DModel is model: Shape3DModel();
	TextEmitter is title: TextEmitter(initial: 'SuitShape3D');
	BoolEmitter is running: BoolEmitter(initial: true);
	BoolEmitter is aboutOpen: BoolEmitter(initial: false);
	TextEmitter is fpsText: TextEmitter(initial: 'FPS: --');
	TextEmitter is versionText: TextEmitter(initial: '');
	TextEmitter is descriptionText: TextEmitter(initial: '');
	ToolbarConfig is toolbarConfig: ToolbarConfig();
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 26.0;

	Mat4 is mOps: Mat4();
	Math is math: Math();
	Int is fpsWindowStartMs: 0;
	Int is frameCount: 0;

	replace Function is init(Shape3DModel is model){
		:model: model;
		title: TextEmitter(initial: model:appName);
		running: BoolEmitter(initial: true);
		aboutOpen: BoolEmitter(initial: false);
		fpsText: TextEmitter(initial: 'FPS: --');
		versionText: TextEmitter(initial: model:appName . ' v' . model:version);
		descriptionText: TextEmitter(initial: model:description);
		toolbarConfig: :buildToolbarConfig();
		fpsWindowStartMs: 0;
		frameCount: 0;
	}

	local Function of ToolbarConfig is buildToolbarConfig(){
		local ToolbarConfig is cfg: ToolbarConfig(heightPt: toolbarHeightPt);

		local MenuConfig is fileMenu: MenuConfig(id: 'file', label: 'File');
		fileMenu:addItem(item: MenuItemConfig(
			id: 'quit',
			label: 'Quit',
			onClick: local Function(){ :requestQuit(); }
		));
		cfg:addMenu(menu: fileMenu);

		local MenuConfig is helpMenu: MenuConfig(id: 'help', label: 'Help');
		helpMenu:addItem(item: MenuItemConfig(
			id: 'about',
			label: 'About',
			onClick: local Function(){ :requestAbout(); }
		));
		cfg:addMenu(menu: helpMenu);

		return cfg;
	}

	Function is requestQuit(){
		running:emit(value: false);
	}

	Function is requestAbout(){
		aboutOpen:emit(value: true);
	}

	## Updates rolling FPS counter and returns the current MVP matrix for [elapsedMs] and viewport [w]x[h].
	Function of Mat4 is stepFrame(Int is elapsedMs, Int is w, Int is h){
		frameCount: frameCount + 1;
		local Int is fpsElapsed: elapsedMs - fpsWindowStartMs;
		if({ fpsElapsed >= 250 }, {
			local Int is fps: (frameCount * 1000) / fpsElapsed;
			fpsText:emit(value: 'FPS: ' . fps);
			fpsWindowStartMs: elapsedMs;
			frameCount: 0;
		});

		local Float is t: math:toFloat(value: elapsedMs) / 1000.0;
		local Float is aspect: if({ h > 0 }, { math:toFloat(value: w) / math:toFloat(value: h) }, { 1.3333 });
		local Mat4 is proj: mOps:perspective(fovRad: 0.785398, aspect: aspect, nearZ: 0.1, farZ: 100.0);
		local Mat4 is view: mOps:translate(tx: 0.0, ty: 0.0, tz: -3.2);
		local Mat4 is rotY: mOps:rotateY(rad: t * 1.1);
		local Mat4 is rotX: mOps:rotateX(rad: t * 0.7);
		local Mat4 is modelMat: rotY:mul(other: rotX);
		local Mat4 is mv: view:mul(other: modelMat);
		return proj:mul(other: mv);
	}
}
