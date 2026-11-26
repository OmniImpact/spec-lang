#! Package suitshape3d:view
#! Absolutely pure composable MVVM View for SuitShape3D.

Class is Shape3DView{
	replace [String] is namespace: ['suitshape3d', 'view'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'mold', CubeMesh],
		['base', 'mold', Mat4],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', Bar],
		['base', 'scrap', VulkanSurface],
		['suitshape3d', 'view', AboutDialog],
		['suitshape3d', 'viewmodel', Shape3DViewModel]
	];

	Function of ToolkitContainer is build(Shape3DViewModel is vm){
		local Theme is theme: Theme(preset: 'light_grayscale');
		local VulkanSurface is surface: VulkanSurface();
		local CubeMesh is cube: CubeMesh();

		return ToolkitContainer(
			title: vm:title,
			running: vm:running,
			targetFps: vm:targetFps,
			theme: theme,
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			useVulkan: true,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			vulkanSurface: surface,
			bottomBar: Bar(
				heightPt: vm:toolbarHeightPt,
				borderSide: 'top',
				rightText: vm:fpsText
			),
			hasBottomBar: true,
			dialog: AboutDialog():build(vm: vm),
			hasDialog: true,
			onInitVulkan: local Function(VulkanSurface is s){
				s:uploadCube(mesh: cube);
			},
			onFrame: local Function(Int is elapsedMs, Int is w, Int is h){
				local Mat4 is mvp: vm:stepFrame(elapsedMs: elapsedMs, w: w, h: h);
				surface:render(mvp: mvp, width: w, height: h);
			},
			onDispose: local Function(){
				cube:dispose();
			}
		);
	}
}
