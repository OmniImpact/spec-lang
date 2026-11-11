#! Package base:sys
#! The filesystem wrapper: the Spec-side names over the file floor's
#! C names.

## Filesystem read, write, and existence inspection with synchronous
## and asynchronous callback execution. The Spec-side names
## (fileRead/fileWrite/...) keep the generic verbs unambiguous under
## the merged as-import scope; the floor carries the C names
## (spec_file_read and friends). The `default`, `onSuccess`, and
## `onError` parameters are optional at call sites.

Class is File{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', File]
	];

	## Reads the entire contents of a file with optional success and error callback handlers.
	##
	## @param path: Filesystem path to the target file.
	## @param onSuccess: Optional callback receiving file contents on successful read: `Function(String is content)`.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @param default: Optional fallback string returned if reading fails or file is absent.
	## @return: File contents on success, or [default].
	## @fallback: Returns [default] and triggers [onError] when the file cannot be opened or read.
	Function of String is fileRead(String is path, Function is onSuccess, Function is onError, String is default){
		return base:sysinternal:File:file_read(path: path, default: default, on_success: onSuccess, on_error: onError);
	}

	## Reads a file asynchronously on a background worker thread, notifying completion via callbacks.
	##
	## @param path: Filesystem path to the target file.
	## @param onSuccess: Callback receiving file contents on successful read: `Function(String is content)`.
	## @param onError: Callback receiving error description on failure: `Function(String is error)`.
	## @param default: Optional fallback string returned if reading fails.
	Function is fileReadAsync(String is path, Function is onSuccess, Function is onError, String is default){
		base:sysinternal:File:file_read_async(path: path, default: default, on_success: onSuccess, on_error: onError);
	}

	## Writes string content to a file with optional success and error callback handlers.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param onSuccess: Optional callback executed on successful write: `Function(Int is bytesWritten)`.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: `true` if write succeeded, `false` otherwise.
	Function of Boolean is fileWrite(String is path, String is content, Function is onSuccess, Function is onError){
		return base:sysinternal:File:file_write(path: path, content: content, on_success: onSuccess, on_error: onError);
	}

	## Appends string content to a file with optional success and error callback handlers.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to append.
	## @param onSuccess: Optional callback executed on successful write: `Function(Int is bytesWritten)`.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: `true` if append succeeded, `false` otherwise.
	Function of Boolean is fileAppend(String is path, String is content, Function is onSuccess, Function is onError){
		return base:sysinternal:File:file_append(path: path, content: content, on_success: onSuccess, on_error: onError);
	}

	## Writes string content to a file asynchronously on a background worker thread.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param onSuccess: Callback executed on successful write: `Function(Int is bytesWritten)`.
	## @param onError: Callback receiving error description on failure: `Function(String is error)`.
	Function is fileWriteAsync(String is path, String is content, Function is onSuccess, Function is onError){
		base:sysinternal:File:file_write_async(path: path, content: content, on_success: onSuccess, on_error: onError);
	}

	## Tests whether a file or directory exists at the specified path.
	##
	## @param path: Path to inspect.
	## @return: `true` if path exists, `false` otherwise.
	Function of Boolean is fileExists(String is path){
		return base:sysinternal:File:file_exists(path: path);
	}

	## Deletes a file at the specified filesystem path.
	##
	## @param path: Path of the file to remove.
	## @return: `true` if removed successfully, `false` otherwise.
	Function of Boolean is fileRemove(String is path){
		return base:sysinternal:File:file_remove(path: path);
	}

	## Creates a unique temporary file securely and returns its path.
	##
	## @param template: Path template ending in XXXXXX (defaults to '/tmp/spec_XXXXXX.c').
	## @return: Created file path, or empty string on failure.
	Function of String is fileTemp(String is template: '/tmp/spec_XXXXXX.c'){
		return base:sysinternal:File:file_temp(template: template);
	}
}
