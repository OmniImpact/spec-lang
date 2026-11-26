#! Package suitshape3d:view
#! Absolutely pure composable MVVM View for SuitShape3D.

Class is Shape3DView{
	replace [String] is namespace: ['suitshape3d', 'view'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'mold', CubeMesh],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', Bar],
		['base', 'scrap', VulkanSurface],
		['suitshape3d', 'view', AboutDialog],
		['suitshape3d', 'viewmodel', Shape3DViewModel]
	];

	Function of ToolkitContainer is build(Shape3DViewModel is vm){
		ToolkitContainer(
			title: vm:title,
			running: vm:running,
			targetFps: vm:targetFps,
			theme: Theme(preset: 'light_grayscale'),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			useVulkan: true,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			vulkanSurface: VulkanSurface(mesh: CubeMesh(), hasMesh: true),
			bottomBar: Bar(
				heightPt: vm:toolbarHeightPt,
				borderSide: 'top',
				rightText: vm:fpsText
			),
			hasBottomBar: true,
			dialog: AboutDialog():build(vm: vm),
			hasDialog: true,
			onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is w, Int is h){
				s:render(mvp: vm:stepFrame(elapsedMs: elapsedMs, w: w, h: h), width: w, height: h);
			}
		)
	}
}
