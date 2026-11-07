#! Package base:io
#! Terminal console output, interactive prompts, and file operations.

## Provides non-blocking, event-driven user input prompts via [InputHandler].
##
## Runtime-managed: the prompt call binds to the
## runtime's interactive prompt loop; no struct is emitted.

Class is Input{
	namespace: ['base', 'io'];

	## Registers an input handler callback to process interactive user console entries.
	##
	## @param handler: An [InputHandler] subclass responding to user input events.
	Function is prompt(InputHandler is handler){
	}
}
