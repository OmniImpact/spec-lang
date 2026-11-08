#! Package base:compiler:parser:loops
#! Applies the fancy escape set (n, t, r, e, ", backslash, backtick, brace;
## unknown escapes pass the escaped character through) over raw content
## without template expansion.

Class of Loop is FancyEscapeLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', TemplateEscapes],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local String is src;
	local Int is pos: 0;
	local String is res: '';

	## The shared escape table.
	local TemplateEscapes is esc: TemplateEscapes:init();

	replace Function is init(String is src){
		self:src: src;
		self:pos: 0;
		self:res: '';
	}

	replace Function of Boolean is evaluate(){
		return self:pos < self:src:length();
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is ch: self:src:charAt(index: self:pos, default: '');
		self:pos: self:pos + 1;
		Conditional:branch(check: { ch == "\\" }, then: {
			Conditional:branch(check: { self:pos < self:src:length() }, then: {
				local String is nextCh: self:src:charAt(index: self:pos, default: '');
				self:pos: self:pos + 1;
				self:res: self:res . self:esc:expand(escaped: nextCh);
			}, otherwise: {
				self:res: self:res . "\\";
			});
			return true;
		});
		self:res: self:res . ch;
		return true;
	}
}
