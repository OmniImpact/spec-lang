#! Package base:suit
#! Normalized key codes dispatched by Suit windows and widgets.

Class is KeyCode{
	replace [String] is namespace: ['base', 'suit'];

	held Int is BACKSPACE: 8;
	held Int is TAB: 9;
	held Int is LINE_FEED: 10;
	held Int is ENTER: 13;
	held Int is ESC: 27;
	held Int is SPACE: 32;
	held Int is DELETE: 127;

	held Int is UP: 1001;
	held Int is DOWN: 1002;
	held Int is LEFT: 1003;
	held Int is RIGHT: 1004;
	held Int is HOME: 1005;
	held Int is END: 1006;
	held Int is PAGE_UP: 1007;
	held Int is PAGE_DOWN: 1008;

	held Function of Boolean is isEnter(Int is key){
		return key == KeyCode:ENTER || key == KeyCode:LINE_FEED;
	}
}
