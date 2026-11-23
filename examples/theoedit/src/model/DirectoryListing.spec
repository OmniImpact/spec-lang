#! Package theoedit:model
#! Pure directory listing model: holds a normalized directory path and its
#! sorted directory, file, and combined display entries.

Class is DirectoryListing{
	namespace: ['theoedit', 'model'];

	String is dir: '.';
	Array of String is dirs: Array();
	Array of String is files: Array();
	Array of String is entries: Array();

	replace Function is init(
		String is dir: '.',
		Array of String is dirs: Array(),
		Array of String is files: Array(),
		Array of String is entries: Array()
	){
		:dir: dir;
		:dirs: dirs;
		:files: files;
		:entries: entries;
	}
}
