#! Package suitshape3d:view
#! Absolutely pure composable MVVM View for SuitShape3D.

Class is Shape3DView{
	replace [String] is namespace: ['suitshape3d', 'view'];

	replace [[String]] is using: [
		['base', 'sew', Rect],
		['base', 'sew', DockSide],
		['base', 'fabric', Theme],
		['base', 'mold', CubeMesh],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', 'toolbar', ToolbarContainer],
		['base', 'scrap', 'toolbar', Toolbar],
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
				borderSide: DockSide:TOP,
				rightText: vm:fpsText
			),
			hasBottomBar: true,
			dialog: AboutDialog():build(vm: vm),
			hasDialog: true,
			onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is w, Int is h){
				local Rect is vb: s:bounds();
				local Int is vw: if({ vb:width > 0 }, { vb:width }, { w });
				local Int is vh: if({ vb:height > 0 }, { vb:height }, { h });
				s:render(mvp: vm:stepFrame(elapsedMs: elapsedMs, w: vw, h: vh), width: w, height: h);
			}
		)
	}
}
