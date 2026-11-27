#! Package base:scrap
#! Severity/category enum for [Toast] banners.

Enum is ToastKind{
	replace [String] is namespace: ['base', 'scrap'];

	INFO,
	SUCCESS,
	WARNING,
	ERROR
}
