#! Package base:io
#! Provides terminal console output, interactive prompts, and file operations.

## Provides filesystem read, write, and existence inspection operations.
class File{

	## Reads the entire contents of a file into a string.
	##
	## @param path: Filesystem path to the target file.
	## @param default: Fallback string returned if reading fails or file is absent.
	## @return: File contents, or [default].
	## @fallback: Returns [default] when the file cannot be opened or read.
	replace Function of String is read(String is path, String is default){
	}

	## Writes string content to a file, overwriting existing contents.
	##
	## @param path: Filesystem path of the destination file.
	## @param content: String data to write.
	## @return: `true` if write succeeded, `false` otherwise.
	replace Function of Boolean is write(String is path, String is content){
	}

	## Tests whether a file or directory exists at the specified path.
	##
	## @param path: Path to inspect.
	## @return: `true` if path exists, `false` otherwise.
	replace Function of Boolean is exists(String is path){
	}

}
