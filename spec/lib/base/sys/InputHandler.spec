#! Package base:sys
#! Terminal console output, interactive prompts, and file operations.

## Callback interface for handling interactive user console input from [Input:prompt].

Class is InputHandler{
	namespace: ['base', 'sys'];

	## Invoked when a line of user input is received.
	##
	## @param action: Input string entered by the user.
	Function is onInput(String is action){
	}
}
