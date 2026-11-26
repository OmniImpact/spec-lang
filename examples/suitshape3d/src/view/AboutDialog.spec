#! Package suitshape3d:view
#! App-specific About dialog composed purely from Scrap/Sew widgets bound to `Shape3DViewModel`.

Class is AboutDialog{
	replace [String] is namespace: ['suitshape3d', 'view'];

	replace [[String]] is using: [
		['base', 'sew', SewNode],
		['base', 'sew', Center],
		['base', 'sew', Column],
		['base', 'scrap', Dialog],
		['base', 'scrap', 'text', TextScrap],
		['suitshape3d', 'viewmodel', Shape3DViewModel]
	];

	Function of Dialog is build(Shape3DViewModel is vm){
		Dialog(
			title: 'About SuitShape3D',
			open: vm:aboutOpen,
			widthPt: 480.0,
			heightPt: 180.0,
			content: Center(
				child: Column(
					gapPt: 10.0,
					children: Array([
						TextScrap(text: vm:versionText, align: 'center') as SewNode,
						TextScrap(text: vm:descriptionText, align: 'center', wrap: true, muted: true) as SewNode
					])
				)
			)
		)
	}
}
