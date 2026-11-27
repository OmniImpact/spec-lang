#! Package base:suit
#! Modifier key bitmasks dispatched with Suit keyboard and pointer events.

Class is KeyMod{
	replace [String] is namespace: ['base', 'suit'];

	held Int is NONE: 0;
	held Int is SHIFT: 1;
	held Int is CTRL: 2;
	held Int is ALT: 4;
	held Int is SUPER: 8;

	held Function of Boolean is hasShift(Int is mods){
		return (mods & KeyMod:SHIFT) != 0;
	}

	held Function of Boolean is hasCtrl(Int is mods){
		return (mods & KeyMod:CTRL) != 0;
	}

	held Function of Boolean is hasAlt(Int is mods){
		return (mods & KeyMod:ALT) != 0;
	}

	held Function of Boolean is hasSuper(Int is mods){
		return (mods & KeyMod:SUPER) != 0;
	}
}
