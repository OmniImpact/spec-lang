#! Package base:io
#! Provides terminal console output, interactive prompts, and file operations.

## Provides non-blocking, event-driven user input prompts via [InputHandler].
class Input{

	## Registers an input handler callback to process interactive user console entries.
	##
	## @param handler: An [InputHandler] subclass responding to user input events.
	replace Function is prompt(InputHandler is handler){
	}

}
