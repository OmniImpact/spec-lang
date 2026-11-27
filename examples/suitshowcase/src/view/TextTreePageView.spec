#! Package suitshowcase:view
#! Showcase page for CodeEditorView (syntax highlighting, word wrap) and TreeView.

Class is TextTreePageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Switch],
		['base', 'scrap', ScrollView],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', CodeEditorView],
		['base', 'scrap', 'tree', TreeNode],
		['base', 'scrap', 'tree', TreeView],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local CodeEditorView is editor: CodeEditorView(
			text: vm:demoCodeText,
			filePath: TextEmitter(initial: 'Demo.spec'),
			wrap: vm:demoWrap,
			lineNumbers: vm:demoNums,
			monospace: vm:demoMono
		);

		local TreeNode is rootA: TreeNode(
			id: 'fabric',
			label: 'base:fabric',
			expanded: true,
			children: Array([
				TreeNode(id: 'color', label: 'Color.spec'),
				TreeNode(id: 'theme', label: 'Theme.spec'),
				TreeNode(id: 'draw', label: 'DrawContext.spec')
			])
		);
		local TreeNode is rootB: TreeNode(
			id: 'scrap',
			label: 'base:scrap',
			expanded: true,
			children: Array([
				TreeNode(id: 'btn', label: 'ScrapButton.spec'),
				TreeNode(id: 'sec', label: 'SectionV.spec / SectionH.spec'),
				TreeNode(id: 'tv', label: 'TextView.spec')
			])
		);
		local TreeView is tree: TreeView(
			roots: Array([rootA, rootB])
		);

		return SectionV(
			children: Array([
				Label(text: 'Text & Tree', heading: true),
				Frame(
					title: 'CodeEditorView',
					child: SectionV(
						children: Array([
							SectionH(
								children: Array([
									SectionH(children: Array([
										Switch(checked: vm:demoWrap:current(), onToggle: local Function(Boolean is v){ vm:demoWrap:emit(value: v); }),
										Label(text: 'Wrap')
									])),
									SectionH(children: Array([
										Switch(checked: vm:demoNums:current(), onToggle: local Function(Boolean is v){ vm:demoNums:emit(value: v); }),
										Label(text: 'Line Numbers')
									])),
									SectionH(children: Array([
										Switch(checked: vm:demoMono:current(), onToggle: local Function(Boolean is v){ vm:demoMono:emit(value: v); }),
										Label(text: 'Mono')
									]))
								])
							),
							Frame(padPt: 0.0, child: ScrollView(child: editor))
						])
					)
				),
				Frame(
					title: 'TreeView',
					child: Frame(padPt: 0.0, child: tree)
				)
			])
		);
	}
}
