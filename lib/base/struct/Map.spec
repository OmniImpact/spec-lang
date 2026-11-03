#! Package base:struct
#! Provides contiguous dynamic collections and associative hash maps.

## An associative key-value map supporting string keys and values.
Class is Map{

	## Looks up a string value by key, returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback string returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	replace Function of String is getString(String is key, String is default){
	}

	## Looks up an integer value by key, returning [default] if not found.
	replace Function of Int is getInt(String is key, Int is default){
	}

	## Looks up a float value by key, returning [default] if not found.
	replace Function of Float is getFloat(String is key, Float is default){
	}

	## Looks up a boolean value by key, returning [default] if not found.
	replace Function of Boolean is getBool(String is key, Boolean is default){
	}

	## Looks up a generic value by key, returning [default] if not found.
	replace Function of Any is get(String is key, Any is default){
	}

	## Inserts or updates an entry in the map.
	##
	## @param key: Entry key string.
	## @param value: Entry value.
	replace Function is set(String is key, Any is value){
	}

	## Determines whether an entry exists for the specified key.
	##
	## @param key: Key to test.
	## @return: `true` if key is present, `false` otherwise.
	replace Function of Boolean is has(String is key){
	}

	## Removes the entry associated with [key].
	##
	## @param key: Key to remove.
	## @return: `true` if removed, `false` if key was not present.
	replace Function of Boolean is remove(String is key){
	}

	## Returns an array containing all keys currently present in the map.
	##
	## @return: [Array] of key strings.
	replace Function of Array of String is keys(){
	}

	## Returns the total number of entries in the map.
	##
	## @return: Entry count integer.
	replace Function of Int is length(){
	}

	## Iterates through each key-value pair in the map, invoking [action] with (key, value).
	##
	## @param action: Function invoked with (key, value) for each entry.
	replace Function is each(Function is action){
	}

}
