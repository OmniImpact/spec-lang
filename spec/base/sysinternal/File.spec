#! Package base:sysinternal
#! The filesystem floor: scalar/byte-pointer PAL declarations.

Class is File{
	replace [String] is namespace: ['base', 'sysinternal'];

	Function of Int is pal_file_read(Int is path_cstr, Int is out_len_addr);
	Function of Int is pal_file_write(Int is path_cstr, Int is data_addr, Int is len, Int is append);
	Function of Boolean is pal_file_exists(Int is path_cstr);
	Function of Boolean is pal_file_remove(Int is path_cstr);
	Function of Int is pal_file_temp(Int is tpl_cstr);
	Function is pal_file_free(Int is ptr);
	Function of Int is pal_last_error_cstr();
}
