#! Package theoedit:vm
#! Focus and hover targets for the main editor screen.

Enum is EditorFocus{
	namespace: ['theoedit', 'vm'],
	NONE,
	EDITOR,
	SAVE,
	SAVE_AS,
	OPEN,
	QUIT,
	PROMPT_SAVE,
	PROMPT_DISCARD,
	PROMPT_CANCEL
}
