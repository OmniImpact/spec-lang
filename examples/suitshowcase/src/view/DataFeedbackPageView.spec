#! Package suitshowcase:view
#! Showcase page demonstrating ListView, TableView, SelectDropdown, TextArea, NumberInput, ProgressBar, Spinner, Badge, Toast, AlertDialog, Popover, Draggable/DropTarget, and reorderable SectionH/SectionV.

Class is DataFeedbackPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Row],
		['base', 'sew', Column],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionH],
		['base', 'scrap', SectionV],
		['base', 'scrap', ListView],
		['base', 'scrap', TableView],
		['base', 'scrap', SelectDropdown],
		['base', 'scrap', TextArea],
		['base', 'scrap', NumberInput],
		['base', 'scrap', ProgressBar],
		['base', 'scrap', Spinner],
		['base', 'scrap', Badge],
		['base', 'scrap', Toast],
		['base', 'scrap', Dialog],
		['base', 'scrap', DialogButton],
		['base', 'scrap', Popover],
		['base', 'scrap', Draggable],
		['base', 'scrap', DropTarget],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	BoolEmitter is alertOpen: BoolEmitter(initial: false);
	BoolEmitter is confirmOpen: BoolEmitter(initial: false);
	Dialog is alertDlg: Dialog();
	Dialog is confirmDlg: Dialog();

	replace Function is init(ShowcaseViewModel is vm: ShowcaseViewModel()){
		:vm: vm;
	}

	Function of SewNode is build(){
		local ListView is demoList: ListView(
			items: Array(['Drag handle to reorder', 'Wayland Native Window', 'Vulkan & Software Canvas', 'Sew Layout Engine', 'Fabric Theme Tokens', 'Scrap Widget Kit']),
			selectedIndex: 0,
			reorderable: true,
			minWidthPt: 220.0,
			heightPt: 140.0,
			onSelect: local Function(Int is idx){
				vm:statusText:emit(value: 'ListView selected row #' . (idx as String));
			},
			onReorder: local Function(Int is fromIdx, Int is toIdx){
				vm:statusText:emit(value: 'ListView reordered ' . (fromIdx as String) . ' -> ' . (toIdx as String));
			}
		);

		local TableView is demoTable: TableView(
			columns: Array(['Widget', 'Package', 'Status']),
			colWidthsPt: Array([130.0, 110.0, 90.0]),
			rows: Array([
				Array(['ListView', 'base:scrap', 'Ready']),
				Array(['TableView', 'base:scrap', 'Ready']),
				Array(['SelectDropdown', 'base:scrap', 'Ready']),
				Array(['TextArea', 'base:scrap', 'Ready']),
				Array(['NumberInput', 'base:scrap', 'Ready']),
				Array(['ProgressBar', 'base:scrap', 'Animated']),
				Array(['Toast', 'base:scrap', 'Auto-hide'])
			]),
			selectedIndex: 0,
			sortable: true,
			heightPt: 150.0,
			onSelect: local Function(Int is idx){
				vm:statusText:emit(value: 'TableView selected row #' . (idx as String));
			},
			onSort: local Function(Int is col, Boolean is asc){
				local String is dir: if({ asc }, { 'ASC' }, { 'DESC' });
				vm:statusText:emit(value: 'TableView sorted col #' . (col as String) . ' (' . dir . ')');
			}
		);

		local SectionH is reorderSegH: SectionH(
			segmented: true,
			reorderable: true,
			options: Array(['Alpha', 'Beta', 'Gamma', 'Delta']),
			selectedIndex: 0,
			itemMinWidthPt: 64.0,
			onSelect: local Function(Int is idx){
				vm:statusText:emit(value: 'Reorderable SectionH selected #' . (idx as String));
			},
			onReorder: local Function(Int is f, Int is t){
				vm:statusText:emit(value: 'SectionH reordered ' . (f as String) . ' -> ' . (t as String));
			}
		);

		local SectionV is reorderSegV: SectionV(
			segmented: true,
			reorderable: true,
			options: Array(['First', 'Second', 'Third']),
			selectedIndex: 0,
			itemMinWidthPt: 100.0,
			onSelect: local Function(Int is idx){
				vm:statusText:emit(value: 'Reorderable SectionV selected #' . (idx as String));
			},
			onReorder: local Function(Int is f, Int is t){
				vm:statusText:emit(value: 'SectionV reordered ' . (f as String) . ' -> ' . (t as String));
			}
		);

		local SelectDropdown is comboStandard: SelectDropdown(
			options: Array(['Light Grayscale', 'Dark Slate', 'Ocean Breeze', 'Warm Sand']),
			selectedIndex: 0,
			minWidthPt: 160.0,
			tooltip: 'Standard SelectDropdown',
			onSelect: local Function(Int is _i, String is val){
				vm:statusText:emit(value: 'SelectDropdown chose: ' . val);
			}
		);

		local SelectDropdown is comboSearch: SelectDropdown(
			options: Array(['Afghanistan', 'Brazil', 'Canada', 'Denmark', 'Finland', 'Germany', 'Japan', 'Norway', 'Spain', 'Sweden']),
			selectedIndex: 2,
			searchable: true,
			minWidthPt: 170.0,
			tooltip: 'Searchable ComboBox — type to filter',
			onSelect: local Function(Int is _i, String is val){
				vm:statusText:emit(value: 'Searchable ComboBox chose: ' . val);
			}
		);

		local ProgressBar is detBar: ProgressBar(value: 0.45, showLabel: true, minWidthPt: 180.0);
		local ProgressBar is indetBar: ProgressBar(indeterminate: true, minWidthPt: 180.0);
		local Spinner is spinWidget: Spinner(sizePt: 28.0, indeterminate: true, label: 'Working...');
		local Spinner is detRing: Spinner(sizePt: 46.0, indeterminate: false, progress: 0.45, showLabel: true);

		local NumberInput is intSpin: NumberInput(
			value: 45.0,
			minVal: 0.0,
			maxVal: 100.0,
			step: 5.0,
			decimals: 0,
			suffix: '%',
			onChange: local Function(Float is v){
				detBar:setValue(next: v / 100.0);
				detRing:setProgress(next: v / 100.0);
				vm:statusText:emit(value: 'Progress set to ' . (v as String) . '%');
			}
		);

		local NumberInput is decSpin: NumberInput(
			value: 1.5,
			minVal: 0.0,
			maxVal: 10.0,
			step: 0.25,
			decimals: 2,
			suffix: 'x',
			onChange: local Function(Float is v){
				vm:statusText:emit(value: 'Scale multiplier: ' . (v as String));
			}
		);

		local TextArea is notesArea: TextArea(
			text: "Multi-line TextArea\nSupports Enter, arrows, Home/End,\nand vertical wheel scrolling.",
			minLines: 4,
			minWidthPt: 260.0,
			onChange: local Function(String is next){
				vm:statusText:emit(value: 'TextArea length: ' . (next:length() as String));
			}
		);

		local Toast is toastBanner: Toast(
			title: 'Toolkit Ready',
			message: 'Click the buttons below to trigger different Toast severities.',
			kind: 0,
			visible: true,
			minWidthPt: 280.0
		);

		local Badge is closableBadge: Badge(
			text: 'Closable Tag',
			closable: true,
			onClose: local Function(){
				vm:statusText:emit(value: 'Closable Badge dismissed');
			}
		);

		:alertDlg: Dialog:compose(
			title: 'Notice',
			message: Column(
				gapPt: 6.0,
				children: Array([
					Label(text: 'Composed Dialog UI', style: TextStyle:H2),
					Label(text: 'This dialog was built with Dialog:compose using a custom SewNode message and DialogButton descriptors.', muted: true)
				])
			),
			buttons: Array([
				DialogButton(
					title: 'OK',
					description: 'Acknowledge and close this notice',
					primary: true,
					onClick: local Function(){
						vm:statusText:emit(value: 'Notice Dialog OK clicked');
					}
				)
			]),
			open: alertOpen,
			theme: vm:activeTheme
		);

		:confirmDlg: Dialog:compose(
			title: 'Confirm Action',
			message: Column(
				gapPt: 6.0,
				children: Array([
					Label(text: 'Apply sample configuration?', style: TextStyle:H2),
					Label(text: 'Choose Confirm to proceed, Apply Draft to test a secondary action, or Cancel to dismiss.', muted: true)
				])
			),
			buttons: Array([
				DialogButton(
					title: 'Cancel',
					description: 'Dismiss without making changes',
					onClick: local Function(){
						vm:statusText:emit(value: 'Dialog cancelled');
					}
				),
				DialogButton(
					title: 'Apply Draft',
					description: 'Save as draft without finalizing',
					onClick: local Function(){
						vm:statusText:emit(value: 'Dialog Apply Draft clicked');
					}
				),
				DialogButton(
					title: 'Confirm',
					description: 'Confirm and apply changes',
					primary: true,
					onClick: local Function(){
						vm:statusText:emit(value: 'Dialog confirmed');
					}
				)
			]),
			open: confirmOpen,
			theme: vm:activeTheme
		);

		local Popover is demoPopover: Popover(
			anchor: ScrapButton(label: 'Toggle Popover', tooltip: 'Opens a draggable floating Popover card'),
			content: Frame(
				title: 'Popover Card',
				child: Column(
					gapPt: 6.0,
					children: Array([
						Label(text: 'Drag the top grip to move.'),
						ScrapButton(label: 'Action inside Popover', onClick: local Function(){
							vm:statusText:emit(value: 'Popover action clicked');
						})
					])
				)
			)
		);

		local TextEmitter is dropLabel: TextEmitter(initial: 'Drop payload here');
		local Draggable is dragTile: Draggable(
			payload: 'WidgetPayload#42',
			dragLabel: 'Dragging: WidgetPayload#42',
			child: Frame(
				padPt: 8.0,
				child: Label(text: 'Drag me (MouseFollow)')
			)
		);
		local DropTarget is dropZone: DropTarget(
			child: Frame(
				padPt: 10.0,
				child: TextScrap(text: dropLabel)
			),
			onDrop: local Function(String is payload){
				dropLabel:emit(value: 'Received: ' . payload);
				vm:statusText:emit(value: 'Dropped: ' . payload);
			}
		);

		return SectionV(
			children: Array([
				Label(text: 'Data, Inputs & Feedback', style: TextStyle:H1),
				TextScrap(text: TextEmitter(initial: 'Reorderable sectionals/lists, sortable TableView, ComboBox, TextArea, NumberInput, Progress, Toast, Dialogs & Drag-Drop.'), muted: true, wrap: true),
				Frame(
					title: 'Reorderable ListView & Sectionals',
					child: Column(
						gapPt: 10.0,
						children: Array([
							Label(text: 'Drag segments horizontally or vertically to reorder:', muted: true),
							reorderSegH,
							Row(
								gapPt: 12.0,
								children: Array([reorderSegV, demoList]),
								flexFlags: Array([false, true])
							)
						])
					)
				),
				Frame(
					title: 'Sortable TableView (DataGrid)',
					child: Column(
						gapPt: 6.0,
						children: Array([
							Label(text: 'Click any column header to sort ASC/DESC; wheel-scroll body:', muted: true),
							demoTable
						])
					)
				),
				Frame(
					title: 'SelectDropdown, NumberInput & TextArea',
					child: Column(
						gapPt: 10.0,
						children: Array([
							Row(gapPt: 10.0, children: Array([comboStandard, comboSearch])),
							Row(gapPt: 10.0, children: Array([intSpin, decSpin])),
							notesArea
						])
					)
				),
				Frame(
					title: 'Progress, Spinner, Badges & Toast',
					child: Column(
						gapPt: 10.0,
						children: Array([
							Row(gapPt: 12.0, children: Array([detBar, indetBar, detRing, spinWidget])),
							Row(
								gapPt: 8.0,
								children: Array([
									Badge(text: 'Default'),
									Badge(text: 'Accent', accent: true),
									closableBadge
								])
							),
							toastBanner,
							Row(
								gapPt: 8.0,
								children: Array([
									ScrapButton(label: 'Info Toast', onClick: local Function(){ toastBanner:show(title: 'Info', message: 'Informational notification', kind: 0); }),
									ScrapButton(label: 'Success Toast', onClick: local Function(){ toastBanner:show(title: 'Saved', message: 'Changes applied cleanly', kind: 1); }),
									ScrapButton(label: 'Warning Toast', onClick: local Function(){ toastBanner:show(title: 'Heads up', message: 'Check configuration values', kind: 2); }),
									ScrapButton(label: 'Error Toast', onClick: local Function(){ toastBanner:show(title: 'Error', message: 'Something went wrong', kind: 3); })
								])
							)
						])
					)
				),
				Frame(
					title: 'Dialogs, Popover & Drag-Drop',
					child: Column(
						gapPt: 10.0,
						children: Array([
							Row(
								gapPt: 8.0,
								children: Array([
									ScrapButton(label: 'Open Notice Dialog', onClick: local Function(){ alertOpen:emit(value: true); }),
									ScrapButton(label: 'Open Action Dialog', onClick: local Function(){ confirmOpen:emit(value: true); }),
									demoPopover
								])
							),
							Row(
								gapPt: 12.0,
								children: Array([dragTile, dropZone])
							)
						])
					)
				)
			])
		);
	}
}
