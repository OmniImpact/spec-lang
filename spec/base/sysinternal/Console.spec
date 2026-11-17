#! Package base:sysinternal
#! The console floor: scalar/byte-pointer stdout/stderr/stdin PAL declarations.

Class is Console{
	namespace: ['base', 'sysinternal'];

	Function is pal_print(Int is data_addr, Int is len);
	Function is pal_print_line(Int is data_addr, Int is len);
	Function is pal_error_line(Int is data_addr, Int is len);
	Function of Int is pal_read_line(Int is out_len_addr);
	Function of Int is pal_read_bytes(Int is dst_addr, Int is count);
	Function is console_binary_mode();
}
