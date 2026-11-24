#! Package base:struct
#! LIFO stack collection implemented over monomorphized Array of T.

## A Last-In, First-Out (LIFO) stack collection of elements.
##
## In accordance with the "Never Null" standard, queries on empty stacks
## return caller-supplied default values of type T.

Class is Stack of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Array of T is storage: Array();
	local T is zeroDefault;

	## Pushes an element onto the top of the stack.
	##
	## @param item: The element to push.
	Function is push(T is item){
		:storage:add(item: item);
	}

	## Removes and returns the top element from the stack.
	##
	## @param default: Fallback returned when the stack is empty.
	## @return: The popped element, or [default].
	Function of T is pop(T is default){
		return :storage:pop(default: default);
	}

	## Returns the top element without removing it.
	##
	## @param default: Fallback returned when the stack is empty.
	## @return: The top element, or [default].
	Function of T is peek(T is default){
		local Int is len: :storage:length();
		if({ len == 0 }, {
			return default;
		});
		return :storage:get(index: len - 1, default: default);
	}

	## Returns the number of elements in the stack.
	##
	## @return: Element count.
	Function of Int is length(){
		return :storage:length();
	}

	## Returns whether the stack has zero elements.
	##
	## @return: true if empty, false otherwise.
	Function of Boolean is isEmpty(){
		return :storage:length() == 0;
	}

	## Removes all elements from the stack.
	Function is clear(){
		:storage:clear();
	}

	## Returns a new Array snapshot containing the stack elements from bottom to top.
	##
	## @return: Snapshot array.
	Function of Array of T is toArray(){
		local Array of T is out: Array();
		local Int is len: :storage:length();
		local Int is i: 0;
		while({ i < len }, {
			out:add(item: :storage:get(index: i, default: :zeroDefault));
			i: i + 1;
		});
		return out;
	}
}
