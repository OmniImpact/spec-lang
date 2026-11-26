#! Package suitshape3d
#! Spinning 3D colored cube rendered via Suit + VulkanSurface + Mold.

Class is SuitShape3D{
	replace [String] is namespace: ['suitshape3d'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'sys', Stderr],
		['base', 'sys', Process],
		['base', 'sys', Time],
		['base', 'math', Math],
		['base', 'struct', Map],
		['base', 'cli', Cli],
		['base', 'suit', SuitWindow],
		['base', 'mold', Mat4],
		['base', 'mold', CubeMesh],
		['base', 'scrap', VulkanSurface]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();

		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);
		local SuitWindow is win: SuitWindow(
			title: 'SuitShape3D',
			width: 800,
			height: 600,
			decorated: true,
			useVulkan: true
		);

		if({ !win:open() }, {
			Stderr():line(text: 'Failed to open window: ':concat(other: win:lastError()));
			Process():exit(status: 1);
		});

		local VulkanSurface is surface: VulkanSurface();
		if({ !surface:attach(window: win) }, {
			Stderr():line(text: 'Failed to initialize Vulkan surface: ':concat(other: surface:lastError()));
			win:close();
			Process():exit(status: 1);
		});

		local CubeMesh is cube: CubeMesh();
		if({ !surface:uploadCube(mesh: cube) }, {
			Stderr():line(text: 'Failed to upload cube mesh: ':concat(other: surface:lastError()));
			cube:dispose();
			surface:dispose();
			win:close();
			Process():exit(status: 1);
		});

		local Time is clock: Time();
		local Math is math: Math();
		local Int is startMs: clock:monotonicMs();
		local Mat4 is mOps: Mat4();
		local Boolean is running: true;

		while({ running && win:poll() }, {
			local Int is key: win:nextKey();
			while({ key != 0 }, {
				if({ key == 27 || key == 113 }, {
					running: false;
				});
				key: win:nextKey();
			});

			local Int is elapsedMs: clock:monotonicMs() - startMs;
			if({ durationMs > 0 && elapsedMs >= durationMs }, {
				running: false;
			});

			if({ running }, {
				local Float is t: math:toFloat(value: elapsedMs) / 1000.0;
				local Int is w: win:width();
				local Int is h: win:height();
				local Float is aspect: if({ h > 0 }, { math:toFloat(value: w) / math:toFloat(value: h) }, { 1.3333 });

				local Mat4 is proj: mOps:perspective(fovRad: 0.785398, aspect: aspect, nearZ: 0.1, farZ: 100.0);
				local Mat4 is view: mOps:translate(tx: 0.0, ty: 0.0, tz: -3.2);
				local Mat4 is rotY: mOps:rotateY(rad: t * 1.1);
				local Mat4 is rotX: mOps:rotateX(rad: t * 0.7);
				local Mat4 is model: rotY:mul(other: rotX);
				local Mat4 is mv: view:mul(other: model);
				local Mat4 is mvp: proj:mul(other: mv);

				if({ !surface:render(mvp: mvp, width: w, height: h) }, {
					Stderr():line(text: 'Vulkan render failed: ':concat(other: surface:lastError()));
					running: false;
				});
			});
		});

		cube:dispose();
		surface:dispose();
		win:close();
	}
}
