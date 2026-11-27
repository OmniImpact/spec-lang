#! Package base:scrap
#! Shared clipboard and default edit context-menu bridge wired by [ToolkitContainer] for editable text widgets.

Class is TextEditBridge{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'scrap', 'menu', MenuItemConfig]
	];

	held TextEditBridge is shared: TextEditBridge();

	String is fallbackClipboard: '';
	Function is clipboardWriter: local Function(String is _text){};
	Function of String is clipboardReader: local Function of String(){ return ''; };
	Function is contextMenuOpener: local Function(Int is _x, Int is _y, Array of MenuItemConfig is _items){};
	Function of Boolean is hostMenuOpenCheck: local Function of Boolean(){ return false; };
	Boolean is hasHost: false;

	Function is bindHost(
		Function is onWrite,
		Function of String is onRead,
		Function is onOpenMenu,
		Function of Boolean is isMenuOpen
	){
		:clipboardWriter: onWrite;
		:clipboardReader: onRead;
		:contextMenuOpener: onOpenMenu;
		:hostMenuOpenCheck: isMenuOpen;
		:hasHost: true;
	}

	Function is writeClipboard(String is text){
		:fallbackClipboard: text;
		if({ hasHost }, {
			local Function is w: clipboardWriter;
			w(text);
		});
	}

	Function of String is readClipboard(){
		if({ hasHost }, {
			local Function of String is r: clipboardReader;
			local String is sysTxt: r();
			if({ sysTxt != '' }, { return sysTxt; });
		});
		return fallbackClipboard;
	}

	Function of Boolean is isHostMenuOpen(){
		if({ !hasHost }, { return false; });
		local Function of Boolean is fn: hostMenuOpenCheck;
		return fn();
	}

	Function is openEditMenu(
		Int is x,
		Int is y,
		Function is onCut,
		Function is onCopy,
		Function is onPaste,
		Function is onSelectAll,
		Boolean is canCut: true,
		Boolean is canCopy: true,
		Boolean is canPaste: true
	){
		if({ !hasHost }, { return; });
		local Function is opener: contextMenuOpener;
		opener(x, y, Array([
			MenuItemConfig(id: 'edit_cut', label: 'Cut', enabled: canCut, onClick: onCut),
			MenuItemConfig(id: 'edit_copy', label: 'Copy', enabled: canCopy, onClick: onCopy),
			MenuItemConfig(id: 'edit_paste', label: 'Paste', enabled: canPaste, onClick: onPaste),
			MenuItemConfig(id: 'edit_select_all', label: 'Select All', enabled: true, onClick: onSelectAll)
		]));
	}
}
