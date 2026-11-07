#! Package base:compiler:parser:loops
#! Splits raw template-string content at unescaped {{ }} pairs into
## literal chunks and hole texts. Quote- and brace-aware inside holes so
## holes may contain string literals and nested braces. Literal escapes
## are processed inline: every backslash consumes its follower, so a {{
## reached in literal state is always a template start.

Class of Loop is TemplateSplitLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', TemplateEscapes],
		['base', 'iterator']
	];

	local String is raw;
	local Int is pos: 0;
	local Boolean is inHole: false;
	local String is lit: '';
	local Array of String is lits: [];
	local String is hole: '';
	local Array of String is holes: [];
	local String is quoteCh: '';
	local Int is braceDepth: 0;

	## The shared escape table.
	local TemplateEscapes is esc: TemplateEscapes:init();

	replace Function is init(String is raw){
		self:raw: raw;
		self:pos: 0;
		self:inHole: false;
		self:lit: '';
		self:lits: [];
		self:hole: '';
		self:holes: [];
		self:quoteCh: '';
		self:braceDepth: 0;
	}

	replace Function of Boolean is evaluate(){
		return self:pos < self:raw:length();
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is ch: self:raw:charAt(index: self:pos, default: '');
		if (!self:inHole) {
			if (ch == "{" && self:pos + 1 < self:raw:length() && self:raw:charAt(index: self:pos + 1, default: '') == "{") {
				self:lits:add(item: self:lit);
				self:lit: '';
				self:inHole: true;
				self:hole: '';
				self:quoteCh: '';
				self:braceDepth: 0;
				self:pos: self:pos + 2;
				return true;
			}
			if (ch == "\\") {
				if (self:pos + 1 < self:raw:length()) {
					local String is nextCh: self:raw:charAt(index: self:pos + 1, default: '');
					self:lit: self:lit . self:esc:expand(escaped: nextCh);
					self:pos: self:pos + 2;
				} else {
					self:lit: self:lit . "\\";
					self:pos: self:pos + 1;
				}
				return true;
			}
			self:lit: self:lit . ch;
			self:pos: self:pos + 1;
			return true;
		}
		if (self:quoteCh != '') {
			if (ch == "\\") {
				self:hole: self:hole . ch;
				self:pos: self:pos + 1;
				if (self:pos < self:raw:length()) {
					self:hole: self:hole . self:raw:charAt(index: self:pos, default: '');
					self:pos: self:pos + 1;
				}
				return true;
			}
			if (ch == self:quoteCh) {
				self:quoteCh: '';
			}
			self:hole: self:hole . ch;
			self:pos: self:pos + 1;
			return true;
		}
		if (ch == '\'' || ch == '"') {
			self:quoteCh: ch;
			self:hole: self:hole . ch;
			self:pos: self:pos + 1;
			return true;
		}
		if (ch == "{") {
			self:braceDepth: self:braceDepth + 1;
			self:hole: self:hole . ch;
			self:pos: self:pos + 1;
			return true;
		}
		if (ch == "}") {
			if (self:braceDepth > 0) {
				self:braceDepth: self:braceDepth - 1;
			} else if (self:pos + 1 < self:raw:length() && self:raw:charAt(index: self:pos + 1, default: '') == "}") {
				self:holes:add(item: self:hole);
				self:hole: '';
				self:inHole: false;
				self:pos: self:pos + 2;
				return true;
			}
			self:hole: self:hole . ch;
			self:pos: self:pos + 1;
			return true;
		}
		self:hole: self:hole . ch;
		self:pos: self:pos + 1;
		return true;
	}
}
