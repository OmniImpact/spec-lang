#! Package base:theo
#! Typed keyboard shortcut descriptor for [Button]s and key-matching widgets.

Class is ShortcutKey{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', KeyEvent],
		['base', 'sys', as Conditional()]
	];

	String is key: '';
	Boolean is ctrl: true;
	Boolean is alt: false;

	replace Function is init(String is key: '', Boolean is ctrl: true, Boolean is alt: false){
		:key: key:toLower();
		:ctrl: ctrl;
		:alt: alt;
	}

	held Function of ShortcutKey is none(){
		return ShortcutKey(key: '', ctrl: false, alt: false);
	}

	held Function of ShortcutKey is ctrl(String is key){
		return ShortcutKey(key: key, ctrl: true, alt: false);
	}

	held Function of ShortcutKey is alt(String is key){
		return ShortcutKey(key: key, ctrl: false, alt: true);
	}

	held Function of ShortcutKey is plain(String is key){
		return ShortcutKey(key: key, ctrl: false, alt: false);
	}

	Function of Boolean is isSet(){
		return key != '';
	}

	Function of Boolean is matches(KeyEvent is event){
		if({ !isSet() }, { return false; });
		if({ event:ctrl != ctrl || event:alt != alt }, { return false; });
		return event:key:toLower() == key || event:kind:toLower() == key;
	}

	Function of Boolean is matchesChar(String is ch){
		if({ !isSet() }, { return false; });
		return ch:toLower() == key;
	}

	Function of String is displayText(){
		if({ !isSet() }, { return ''; });
		local String is up: key:toUpper();
		if({ ctrl && alt }, { return "Ctrl+Alt+{{up}}"; });
		if({ ctrl }, { return "Ctrl+{{up}}"; });
		if({ alt }, { return "Alt+{{up}}"; });
		return up;
	}
}
