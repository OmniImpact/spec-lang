#! Package base:sysinternal
#! Filesystem directory floor: scalar/byte-pointer PAL declarations.

Class is Dir{
	replace [String] is namespace: ['base', 'sysinternal'];

	Function of Int is pal_dir_open_cstr(Int is path_cstr);
	Function of Int is pal_dir_next(Int is handle);
	Function is pal_dir_close(Int is handle);
	Function of Int is pal_last_error_cstr();
	Function of Int is pal_exe_dir(Int is buf_addr, Int is buf_size);
	Function of Int is pal_file_size_cstr(Int is path_cstr);
}
