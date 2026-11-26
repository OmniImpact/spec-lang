#! Package base:fabric
#! Built-in theme presets exposed as a typed enum for UI theme selection.

Enum is ThemePreset{
	replace [String] is namespace: ['base', 'fabric'];

	LIGHT,
	DARK
}
