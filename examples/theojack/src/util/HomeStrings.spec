#! Package theojack:util
#! Centralized strings and card art for the TheoJack home screen.

Class is HomeStrings{
	replace [String] is namespace: ['theojack', 'util'];

	held Int is CARD_WIDTH: 11;

	held String is HERO_CARD: "╭─────────╮\n│ A       │\n│         │\n│    ♠    │\n│         │\n│       A │\n╰─────────╯";

	held String is MENU_PLAY: 'Play';
	held String is MENU_RULES: 'Rules';
	held String is MENU_ABOUT: 'About';
	held String is MENU_QUIT: 'Quit';

	held String is ABOUT_TITLE: ' About ';
	held String is ABOUT_BODY: "TheoJack is a Blackjack game\nwritten in Spec using the\nTheo TUI toolkit.";
	held String is ABOUT_CLOSE: 'Close';
}
