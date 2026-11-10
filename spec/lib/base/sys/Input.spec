#! Package base:sys
#! The console input wrapper over the console floor's read-line
#! primitive.

## Interactive console input. `consIn` reads one line and hands it to
## the handler — the console-in half of the console I/O pair
## (`consOut`/`consIn`).

Class is Input{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', InputHandler],
		['base', 'sysinternal', Console]
	];

	## Reads one line of console input and dispatches it to
	## [handler]'s onInput; at end of input nothing is dispatched.
	##
	## @param handler: An [InputHandler] subclass responding to user input events.
	Function is consIn(InputHandler is handler){
		base:sysinternal:Console:read_line(on_line: local Function(String is text){
			handler:onInput(text);
		});
	}
}
