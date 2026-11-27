#! Package suitshowcase:view
#! Showcase page demonstrating embedded offscreen Vulkan 3D rendering with transparent background and sphere-in-cube scene.

Class is VulkanPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Row],
		['base', 'sew', Column],
		['base', 'fabric', Color],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', SectionV],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', VulkanViewport],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();

	replace Function is init(ShowcaseViewModel is vm: ShowcaseViewModel()){
		:vm: vm;
	}

	Function of SewNode is build(){
		local VulkanViewport is cubeView: VulkanViewport(
			widthPt: 170.0,
			heightPt: 170.0,
			sphereInCube: false,
			tooltip: 'Spinning Vulkan 3D cube (transparent background)'
		);

		local Color is initSphereCol: Color(r: 175, g: 178, b: 184);
		local VulkanViewport is sphereCubeView: VulkanViewport(
			widthPt: 170.0,
			heightPt: 170.0,
			sphereInCube: true,
			sphereColor: initSphereCol,
			tooltip: 'Gray sphere inside inward-facing colored Vulkan cube room'
		);

		local ColorSwatchDropdown is sphereColorPicker: ColorSwatchDropdown(
			color: initSphereCol,
			compactPicker: true,
			tooltip: 'Pick sphere color',
			onChange: local Function(Color is nextCol){
				sphereCubeView:setSphereColor(next: nextCol);
				vm:statusText:emit(value: 'Vulkan sphere color: ' . nextCol:toHex());
			}
		);

		return SectionV(
			children: Array([
				Label(text: '3D Vulkan', style: TextStyle:H1),
				TextScrap(text: TextEmitter(initial: 'Offscreen Vulkan 3D viewports composited with transparent background.'), muted: true, wrap: true),
				Row(
					gapPt: 16.0,
					children: Array([
						Column(
							gapPt: 6.0,
							children: Array([
								Label(text: 'Spinning Cube', style: TextStyle:H3),
								cubeView
							])
						),
						Frame(
							title: 'Sphere Inside Colored Cube',
							child: Column(
								gapPt: 8.0,
								children: Array([
									sphereCubeView,
									Row(
										gapPt: 8.0,
										children: Array([
											Label(text: 'Sphere Color:'),
											sphereColorPicker
										])
									)
								])
							)
						)
					])
				)
			])
		);
	}
}
