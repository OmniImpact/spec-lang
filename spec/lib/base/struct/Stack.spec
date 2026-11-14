#! Package base:struct
#! LIFO stack collection implemented over the sysinternal vector floor.

## A Last-In, First-Out (LIFO) stack collection of elements.
##
## Implemented purely in Spec over the base:sys:Vector floor.
## In accordance with the "Never Null" standard, queries on empty stacks
## return caller-supplied default values.

Class is Stack of T{
	namespace: ['base', 'struct'];

	replace Array of Array of String is using: [
		['base', 'sys', as Vector()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Any is storage: [];

	## Pushes an element onto the top of the stack.
	##
	## @param item: The element to push.
	Function is push(T is item){
		Vector:vecAdd(v: self:storage, item: item);
	}

	## Removes and returns the top element from the stack.
	##
	## @param default: Fallback returned when the stack is empty.
	## @return: The popped element, or [default].
	Function of T is pop(Any is default){
		return Vector:vecPopLast(v: self:storage, def: default);
	}

	## Returns the top element without removing it.
	##
	## @param default: Fallback returned when the stack is empty.
	## @return: The top element, or [default].
	Function of T is peek(Any is default){
		local Int is len: Vector:vecLength(v: self:storage);
		if({ len == 0 }, {
			return default;
		});
		return Vector:vecGetAt(v: self:storage, idx: len - 1, def: default);
	}

	## Returns the number of elements in the stack.
	##
	## @return: Element count.
	Function of Int is length(){
		return Vector:vecLength(v: self:storage);
	}

	## Returns whether the stack has zero elements.
	##
	## @return: true if empty, false otherwise.
	Function of Boolean is isEmpty(){
		return Vector:vecLength(v: self:storage) == 0;
	}

	## Removes all elements from the stack.
	Function is clear(){
		Vector:vecClear(v: self:storage);
	}

	## Returns a new Array snapshot containing the stack elements from bottom to top.
	##
	## @return: Snapshot array.
	Function of Array of T is toArray(){
		local Array of T is out: [];
		local Int is len: Vector:vecLength(v: self:storage);
		local Int is i: 0;
		while({ i < len }, {
			out:add(item: Vector:vecGetAt(v: self:storage, idx: i, def: ''));
			i: i + 1;
		});
		return out;
	}
}
