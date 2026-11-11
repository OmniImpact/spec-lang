#! Package base:sysinternal
#! The filesystem floor: the fd-level operations bound to C by the
#! naming convention. The C names are the internal provenance — the
#! base:sys File wrapper decides what WE call them on the Spec side
#! (fileRead/fileWrite/fileExists/fileRemove and the async pair).

Class is File{
	namespace: ['base', 'sysinternal'];

	## Reads the entire contents of a file; on failure hands the error
	## description to [on_error] (when given) and yields [default].
	## Bound to `spec_file_read`.
	##
	## @param path: Filesystem path to the target file.
	## @param default: Fallback string returned when the read fails.
	## @param on_success: Optional callback receiving the contents.
	## @param on_error: Optional callback receiving the error description.
	## @return: File contents on success, or [default].
	Function of String is file_read(String is path, String is default, Function is on_success, Function is on_error);

	## Reads a file asynchronously on a background worker thread.
	## Bound to `spec_file_read_async`.
	##
	## @param path: Filesystem path to the target file.
	## @param default: Fallback string returned when the read fails.
	## @param on_success: Callback receiving the contents.
	## @param on_error: Callback receiving the error description.
	Function is file_read_async(String is path, String is default, Function is on_success, Function is on_error);

	## Writes string content to a file. Bound to `spec_file_write`.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param on_success: Optional callback executed on success.
	## @param on_error: Optional callback receiving the error description.
	## @return: `true` if the write succeeded, `false` otherwise.
	Function of Boolean is file_write(String is path, String is content, Function is on_success, Function is on_error);

	## Appends string content to a file. Bound to `spec_file_append`.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to append.
	## @param on_success: Optional callback executed on success.
	## @param on_error: Optional callback receiving the error description.
	## @return: `true` if the append succeeded, `false` otherwise.
	Function of Boolean is file_append(String is path, String is content, Function is on_success, Function is on_error);

	## Writes string content to a file asynchronously. Bound to
	## `spec_file_write_async`.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @param on_success: Callback executed on success.
	## @param on_error: Callback receiving the error description.
	Function is file_write_async(String is path, String is content, Function is on_success, Function is on_error);

	## Tests whether a file or directory exists at the specified path.
	## Bound to `spec_file_exists`.
	##
	## @param path: Path to inspect.
	## @return: `true` if path exists, `false` otherwise.
	Function of Boolean is file_exists(String is path);

	## Deletes a file at the specified filesystem path. Bound to
	## `spec_file_remove`.
	##
	## @param path: Path of the file to remove.
	## @return: `true` if removed successfully, `false` otherwise.
	Function of Boolean is file_remove(String is path);

	## Creates a unique temporary file from template and returns its path,
	## or empty string on failure. Bound to `spec_file_temp`.
	##
	## @param template: Path template ending in XXXXXX.
	## @return: Path to created temporary file, or empty string.
	Function of String is file_temp(String is template);
}
