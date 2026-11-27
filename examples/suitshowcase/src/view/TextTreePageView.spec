#! Package suitshowcase:view
#! Showcase page for CodeEditorView (syntax highlighting, word wrap) and TreeView.

Class is TextTreePageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
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
			id: 'spec',
			label: 'Spec Repository',
			expanded: true,
			children: Array([
				TreeNode(
					id: 'lib',
					label: 'spec/lib/base',
					expanded: true,
					children: Array([
						TreeNode(
							id: 'fabric',
							label: 'fabric',
							expanded: true,
							children: Array([
								TreeNode(id: 'color', label: 'Color.spec'),
								TreeNode(id: 'theme', label: 'Theme.spec'),
								TreeNode(id: 'draw', label: 'DrawContext.spec')
							])
						),
						TreeNode(
							id: 'sew',
							label: 'sew',
							expanded: false,
							children: Array([
								TreeNode(id: 'node', label: 'SewNode.spec'),
								TreeNode(id: 'col', label: 'Column.spec'),
								TreeNode(id: 'row', label: 'Row.spec'),
								TreeNode(id: 'nav', label: 'nav/NavStack.spec')
							])
						),
						TreeNode(
							id: 'scrap',
							label: 'scrap',
							expanded: true,
							children: Array([
								TreeNode(id: 'btn', label: 'ScrapButton.spec'),
								TreeNode(id: 'slider', label: 'Slider.spec'),
								TreeNode(id: 'csel', label: 'ColorSelector.spec'),
								TreeNode(id: 'tv', label: 'text/TextView.spec')
							])
						)
					])
				),
				TreeNode(
					id: 'examples',
					label: 'examples',
					expanded: true,
					children: Array([
						TreeNode(
							id: 'specedit',
							label: 'specedit',
							expanded: false,
							children: Array([
								TreeNode(id: 'se_main', label: 'SpecEdit.spec'),
								TreeNode(id: 'se_vm', label: 'EditorViewModel.spec')
							])
						),
						TreeNode(
							id: 'suitshowcase',
							label: 'suitshowcase',
							expanded: true,
							children: Array([
								TreeNode(id: 'ss_main', label: 'SuitShowcase.spec'),
								TreeNode(id: 'ss_view', label: 'ShowcaseView.spec')
							])
						)
					])
				)
			])
		);
		local TreeView is tree: TreeView(
			roots: Array([rootA])
		);

		return SectionV(
			children: Array([
				Label(text: 'Text & Tree', style: TextStyle:H1),
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
							Frame(padPt: 0.0, child: ScrollView(heightPt: 150.0, child: editor))
						])
					)
				),
				Frame(
					title: 'TreeView',
					child: Frame(padPt: 0.0, child: ScrollView(heightPt: 140.0, child: tree))
				)
			])
		);
	}
}
