#! Package base:cleo
#! Half-block 24-bit TrueColor pixel canvas (2 vertical pixels per terminal row).

Class is CleoImage{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Int is pixelWidth: 0;
	Int is pixelHeight: 0;
	Array of Int is pixels: [];

	replace Function is init(Int is pixelWidth, Int is pixelHeight){
		self:pixelWidth: pixelWidth;
		self:pixelHeight: pixelHeight;
		self:pixels: [];
		local Int is total: pixelWidth * pixelHeight * 3;
		local Int is i: 0;
		while({ i < total }, {
			self:pixels:add(item: 0);
			i: i + 1;
		});
	}

	Function is setPixel(Int is x, Int is y, Int is r, Int is g, Int is b){
		if({ x < 0 || x >= self:pixelWidth || y < 0 || y >= self:pixelHeight }, {
			return;
		});
		local Int is base: ((y * self:pixelWidth) + x) * 3;
		self:pixels:set(index: base, value: r);
		self:pixels:set(index: base + 1, value: g);
		self:pixels:set(index: base + 2, value: b);
	}

	Function of Array of String is renderLines(){
		local Array of String is rows: [];
		local Int is y: 0;
		while({ y < self:pixelHeight }, {
			local String is row: '';
			local Int is x: 0;
			while({ x < self:pixelWidth }, {
				local Int is topBase: ((y * self:pixelWidth) + x) * 3;
				local Int is tr: self:pixels:get(index: topBase, default: 0);
				local Int is tg: self:pixels:get(index: topBase + 1, default: 0);
				local Int is tb: self:pixels:get(index: topBase + 2, default: 0);
				local Int is br: 0;
				local Int is bg: 0;
				local Int is bb: 0;
				if({ (y + 1) < self:pixelHeight }, {
					local Int is botBase: (((y + 1) * self:pixelWidth) + x) * 3;
					br: self:pixels:get(index: botBase, default: 0);
					bg: self:pixels:get(index: botBase + 1, default: 0);
					bb: self:pixels:get(index: botBase + 2, default: 0);
				});
				row: row . Ansi:fgRgb(r: tr, g: tg, b: tb) . Ansi:bgRgb(r: br, g: bg, b: bb) . '▀';
				x: x + 1;
			});
			row: row . Ansi:reset();
			rows:add(item: row);
			y: y + 2;
		});
		return rows;
	}
}
