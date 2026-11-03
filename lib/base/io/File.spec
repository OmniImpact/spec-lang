#! Package base:io
#! Provides terminal console output, interactive prompts, and file operations.

## Provides filesystem read, write, and existence inspection operations with synchronous and asynchronous callback execution.
Class is File{

	## Reads the entire contents of a file with optional success and error callback handlers.
	##
	## @param path: Filesystem path to the target file.
	## @param onSuccess: Optional callback receiving file contents on successful read: `Function(String is content)`.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @param default: Optional fallback string returned if reading fails or file is absent.
	## @return: File contents on success, or [default].
	## @fallback: Returns [default] and triggers [onError] when the file cannot be opened or read.
	Function of String is read(String is path, Function is onSuccess, Function is onError, String is default){
	}

	## Reads a file asynchronously on a background worker thread, notifying completion via callbacks.
	##
	## @param path: Filesystem path to the target file.
	## @param onSuccess: Callback receiving file contents on successful read: `Function(String is content)`.
	## @param onError: Callback receiving error description on failure: `Function(String is error)`.
	## @param default: Optional fallback string returned if reading fails.
	Function is readAsync(String is path, Function is onSuccess, Function is onError, String is default){
	}

	## Writes string content to a file with optional success and error callback handlers.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param onSuccess: Optional callback executed on successful write: `Function(Int is bytesWritten)`.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: `true` if write succeeded, `false` otherwise.
	Function of Boolean is write(String is path, String is content, Function is onSuccess, Function is onError){
	}

	## Writes string content to a file asynchronously on a background worker thread.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param onSuccess: Callback executed on successful write: `Function(Int is bytesWritten)`.
	## @param onError: Callback receiving error description on failure: `Function(String is error)`.
	Function is writeAsync(String is path, String is content, Function is onSuccess, Function is onError){
	}

	## Tests whether a file or directory exists at the specified path.
	##
	## @param path: Path to inspect.
	## @return: `true` if path exists, `false` otherwise.
	Function of Boolean is exists(String is path){
	}

	## Deletes a file at the specified filesystem path.
	##
	## @param path: Path of the file to remove.
	## @return: `true` if removed successfully, `false` otherwise.
	Function of Boolean is remove(String is path){
	}

}
