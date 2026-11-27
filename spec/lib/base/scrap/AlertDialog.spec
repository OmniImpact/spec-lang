#! Package base:scrap
#! Convenience builders for standard Alert and Confirm modal/non-blocking [Dialog] windows.

Class is AlertDialog{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'fabric', Theme],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'sew', Padding],
		['base', 'sew', Scale],
		['base', 'scrap', Dialog],
		['base', 'scrap', Label],
		['base', 'scrap', Clickable]
	];

	held AlertDialog is shared: AlertDialog();

	## Builds an alert [Dialog] with a message and an OK button.
	Function of Dialog is alert(
		String is title: 'Alert',
		String is message: '',
		BoolEmitter is open: BoolEmitter(initial: false),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		String is okLabel: 'OK',
		Function is onOk: local Function(){}
	){
		local Clickable is okBtn: Clickable(
			label: okLabel,
			selected: true,
			minWidthPt: 88.0,
			onClick: local Function(){
				open:set(val: false);
				onOk();
			}
		);
		local SewNode is body: Padding(
			allPt: 16.0,
			child: Column(
				children: Array([
					Label(text: message),
					Row(children: Array([okBtn]), gapPt: 8.0)
				]),
				flexFlags: Array([true, false]),
				gapPt: 16.0
			)
		);
		return Dialog(
			title: title,
			open: open,
			theme: theme,
			scale: scale,
			widthPt: 400.0,
			heightPt: 150.0,
			minWidthPt: 280.0,
			minHeightPt: 120.0,
			content: body,
			hasContent: true
		);
	}

	## Builds a confirmation [Dialog] with Cancel and Confirm buttons.
	Function of Dialog is confirm(
		String is title: 'Confirm',
		String is message: '',
		BoolEmitter is open: BoolEmitter(initial: false),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		String is confirmLabel: 'Confirm',
		String is cancelLabel: 'Cancel',
		Function is onConfirm: local Function(){},
		Function is onCancel: local Function(){}
	){
		local Clickable is cancelBtn: Clickable(
			label: cancelLabel,
			minWidthPt: 88.0,
			onClick: local Function(){
				open:set(val: false);
				onCancel();
			}
		);
		local Clickable is confirmBtn: Clickable(
			label: confirmLabel,
			selected: true,
			minWidthPt: 88.0,
			onClick: local Function(){
				open:set(val: false);
				onConfirm();
			}
		);
		local SewNode is body: Padding(
			allPt: 16.0,
			child: Column(
				children: Array([
					Label(text: message),
					Row(children: Array([cancelBtn, confirmBtn]), gapPt: 8.0)
				]),
				flexFlags: Array([true, false]),
				gapPt: 16.0
			)
		);
		return Dialog(
			title: title,
			open: open,
			theme: theme,
			scale: scale,
			widthPt: 420.0,
			heightPt: 160.0,
			minWidthPt: 300.0,
			minHeightPt: 120.0,
			content: body,
			hasContent: true
		);
	}
}
